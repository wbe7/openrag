"""Service for transcribing audio/video files using OpenAI Whisper API."""

import os
import math
import tempfile
import subprocess
from typing import List

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Whisper API max file size is 25MB
WHISPER_MAX_FILE_SIZE = 25 * 1024 * 1024

# Audio/video extensions that should be transcribed
MEDIA_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".webm", ".weba", ".mpeg", ".mpga", ".oga", ".ogg"}


def _fmt_ts(seconds: float) -> str:
    """Format seconds as HH:MM:SS,mmm (SRT timestamp format)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def is_media_file(file_path: str) -> bool:
    """Check if a file is an audio/video file that should be transcribed."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in MEDIA_EXTENSIONS


def _split_audio(file_path: str, max_size: int = WHISPER_MAX_FILE_SIZE) -> List[str]:
    """Split an audio/video file into chunks under the Whisper API size limit.

    Uses ffmpeg to extract audio and split into segments. Returns a list of
    temporary file paths. Caller is responsible for cleanup.
    """
    file_size = os.path.getsize(file_path)
    if file_size <= max_size:
        return [file_path]

    # Get duration using ffprobe
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path],
            capture_output=True, text=True, timeout=30,
        )
        import json
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except Exception as e:
        logger.error("ffprobe failed, cannot split file", error=str(e))
        raise ValueError(
            f"Cannot determine media duration for splitting. "
            f"File is {file_size / 1024 / 1024:.1f}MB (limit: 25MB). "
            f"Install ffmpeg to enable automatic splitting."
        ) from e

    # Calculate number of segments needed (with safety margin)
    num_segments = math.ceil(file_size / (max_size * 0.9))
    segment_duration = duration / num_segments

    logger.info(
        "Splitting media file",
        file_size_mb=f"{file_size / 1024 / 1024:.1f}",
        duration_s=f"{duration:.1f}",
        num_segments=num_segments,
        segment_duration_s=f"{segment_duration:.1f}",
    )

    temp_dir = tempfile.mkdtemp(prefix="openrag_media_")
    segment_paths = []

    for i in range(num_segments):
        start = i * segment_duration
        segment_path = os.path.join(temp_dir, f"segment_{i:03d}.mp3")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", file_path,
                    "-ss", str(start), "-t", str(segment_duration),
                    "-vn",  # strip video
                    "-acodec", "libmp3lame", "-b:a", "128k",
                    segment_path,
                ],
                capture_output=True, text=True, timeout=300,
                check=True,
            )
            segment_paths.append(segment_path)
        except Exception as e:
            logger.error("ffmpeg segment extraction failed", segment=i, error=str(e))
            # Cleanup on failure
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    return segment_paths


async def transcribe_media(file_path: str) -> dict:
    """Transcribe an audio/video file using the OpenAI Whisper API.

    Returns a dict matching the structure expected by the RAG pipeline:
    {
        "id": <file_hash>,
        "filename": <basename>,
        "mimetype": <audio/video mimetype>,
        "chunks": [
            {
                "page": <segment_number>,
                "type": "transcript",
                "text": <transcript_text>,
                "timestamp_start": <float_seconds>,
                "timestamp_end": <float_seconds>,
            },
            ...
        ]
    }
    """
    from config.settings import clients
    from utils.hash_utils import hash_id
    import mimetypes
    import shutil

    file_hash = hash_id(file_path)
    filename = os.path.basename(file_path)
    mimetype = mimetypes.guess_type(filename)[0] or "audio/mpeg"

    # Split if necessary
    segment_paths = _split_audio(file_path)
    is_split = segment_paths[0] != file_path
    time_offset = 0.0

    chunks = []
    chunk_index = 0

    try:
        for seg_idx, seg_path in enumerate(segment_paths):
            logger.info(
                "Transcribing segment",
                segment=seg_idx + 1,
                total_segments=len(segment_paths),
                file=os.path.basename(seg_path),
            )

            with open(seg_path, "rb") as audio_file:
                # Use verbose_json to get segment-level timestamps
                response = await clients.patched_embedding_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            # Process segments from the response
            segments = getattr(response, "segments", None) or []

            if not segments:
                # Fallback: if no segments returned, create a single chunk from the full text
                full_text = getattr(response, "text", "")
                if full_text.strip():
                    chunks.append({
                        "page": chunk_index + 1,
                        "type": "transcript",
                        "text": full_text.strip(),
                        "timestamp_start": time_offset,
                        "timestamp_end": time_offset + getattr(response, "duration", 0.0),
                    })
                    chunk_index += 1
            else:
                # Group segments into ~1000 char chunks for consistent embedding sizes
                current_text = ""
                current_start = None

                for seg in segments:
                    seg_text = seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", "")
                    seg_start = (seg.get("start", 0.0) if isinstance(seg, dict) else getattr(seg, "start", 0.0)) + time_offset
                    seg_end = (seg.get("end", 0.0) if isinstance(seg, dict) else getattr(seg, "end", 0.0)) + time_offset

                    if current_start is None:
                        current_start = seg_start

                    if len(current_text) + len(seg_text) > 1000 and current_text:
                        chunks.append({
                            "page": chunk_index + 1,
                            "type": "transcript",
                            "text": current_text.strip(),
                            "timestamp_start": round(current_start, 2),
                            "timestamp_end": round(seg_start, 2),
                        })
                        chunk_index += 1
                        current_text = seg_text
                        current_start = seg_start
                    else:
                        current_text += seg_text

                # Flush remaining text
                if current_text.strip():
                    chunks.append({
                        "page": chunk_index + 1,
                        "type": "transcript",
                        "text": current_text.strip(),
                        "timestamp_start": round(current_start, 2),
                        "timestamp_end": round(seg_end, 2),
                    })
                    chunk_index += 1

            # Update time offset for next segment
            segment_duration = getattr(response, "duration", 0.0)
            time_offset += segment_duration

    finally:
        # Clean up split segments
        if is_split and segment_paths:
            temp_dir = os.path.dirname(segment_paths[0])
            shutil.rmtree(temp_dir, ignore_errors=True)

    # Prepend SRT-style timestamps to each chunk's text so the LLM sees
    # temporal context when the chunk is retrieved during RAG
    for chunk in chunks:
        start = chunk["timestamp_start"]
        end = chunk["timestamp_end"]
        chunk["text"] = f"[{_fmt_ts(start)} --> {_fmt_ts(end)}]\n{chunk['text']}"

    if not chunks:
        chunks.append({
            "page": 1,
            "type": "transcript",
            "text": "",
            "timestamp_start": 0.0,
            "timestamp_end": 0.0,
        })

    logger.info(
        "Transcription complete",
        filename=filename,
        total_chunks=len(chunks),
        total_duration_s=round(time_offset, 2),
    )

    return {
        "id": file_hash,
        "filename": filename,
        "mimetype": mimetype,
        "chunks": chunks,
    }
