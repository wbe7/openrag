"""Tests for the media transcription service."""

import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


from services.transcription_service import (
    is_media_file,
    MEDIA_EXTENSIONS,
    transcribe_media,
)


class TestIsMediaFile:
    def test_mp3(self):
        assert is_media_file("podcast.mp3") is True

    def test_mp4(self):
        assert is_media_file("video.mp4") is True

    def test_m4a(self):
        assert is_media_file("audio.m4a") is True

    def test_wav(self):
        assert is_media_file("recording.wav") is True

    def test_webm(self):
        assert is_media_file("clip.webm") is True

    def test_pdf_is_not_media(self):
        assert is_media_file("document.pdf") is False

    def test_txt_is_not_media(self):
        assert is_media_file("notes.txt") is False

    def test_docx_is_not_media(self):
        assert is_media_file("report.docx") is False

    def test_case_insensitive(self):
        assert is_media_file("AUDIO.MP3") is True
        assert is_media_file("Video.MP4") is True

    def test_all_media_extensions(self):
        for ext in MEDIA_EXTENSIONS:
            assert is_media_file(f"file{ext}") is True


class TestTranscribeMedia:
    @pytest.fixture
    def small_mp3(self, tmp_path):
        """Create a small test file that pretends to be an mp3."""
        mp3_path = tmp_path / "test.mp3"
        # Write some bytes so the file exists and has a size
        mp3_path.write_bytes(b"\x00" * 1024)
        return str(mp3_path)

    @pytest.mark.asyncio
    async def test_transcribe_returns_correct_structure(self, small_mp3):
        """Test that transcribe_media returns the expected dict structure."""
        # Mock the Whisper API response
        mock_segment = MagicMock()
        mock_segment.text = "Hello world, this is a test transcription."
        mock_segment.start = 0.0
        mock_segment.end = 5.0

        mock_response = MagicMock()
        mock_response.segments = [mock_segment]
        mock_response.duration = 5.0
        mock_response.text = "Hello world, this is a test transcription."

        mock_audio_client = AsyncMock()
        mock_audio_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        mock_clients = MagicMock()
        mock_clients.patched_embedding_client = mock_audio_client

        with patch("config.settings.clients", mock_clients):
            result = await transcribe_media(small_mp3)

        assert "id" in result
        assert "filename" in result
        assert "mimetype" in result
        assert "chunks" in result
        assert result["filename"] == "test.mp3"
        assert len(result["chunks"]) > 0

    @pytest.mark.asyncio
    async def test_chunks_have_timestamps(self, small_mp3):
        """Test that each chunk has timestamp_start and timestamp_end."""
        mock_segment_1 = MagicMock()
        mock_segment_1.text = "First segment of the audio."
        mock_segment_1.start = 0.0
        mock_segment_1.end = 3.0

        mock_segment_2 = MagicMock()
        mock_segment_2.text = "Second segment continues here."
        mock_segment_2.start = 3.0
        mock_segment_2.end = 6.0

        mock_response = MagicMock()
        mock_response.segments = [mock_segment_1, mock_segment_2]
        mock_response.duration = 6.0

        mock_audio_client = AsyncMock()
        mock_audio_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        mock_clients = MagicMock()
        mock_clients.patched_embedding_client = mock_audio_client

        with patch("config.settings.clients", mock_clients):
            result = await transcribe_media(small_mp3)

        for chunk in result["chunks"]:
            assert "timestamp_start" in chunk
            assert "timestamp_end" in chunk
            assert "text" in chunk
            assert chunk["type"] == "transcript"
            assert isinstance(chunk["timestamp_start"], float)
            assert isinstance(chunk["timestamp_end"], float)

    @pytest.mark.asyncio
    async def test_chunks_grouped_by_size(self, small_mp3):
        """Test that small segments are grouped into larger chunks."""
        # Create many small segments that should be grouped
        segments = []
        for i in range(20):
            seg = MagicMock()
            seg.text = f" Segment number {i} with some text content."
            seg.start = float(i * 2)
            seg.end = float(i * 2 + 2)
            segments.append(seg)

        mock_response = MagicMock()
        mock_response.segments = segments
        mock_response.duration = 40.0

        mock_audio_client = AsyncMock()
        mock_audio_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        mock_clients = MagicMock()
        mock_clients.patched_embedding_client = mock_audio_client

        with patch("config.settings.clients", mock_clients):
            result = await transcribe_media(small_mp3)

        # 20 segments with ~40 chars each = ~800 chars total, should fit in 1 chunk
        assert len(result["chunks"]) < 20
        # All text should be present
        all_text = " ".join(c["text"] for c in result["chunks"])
        for i in range(20):
            assert f"Segment number {i}" in all_text

    @pytest.mark.asyncio
    async def test_fallback_when_no_segments(self, small_mp3):
        """Test fallback when Whisper returns no segments."""
        mock_response = MagicMock()
        mock_response.segments = []
        mock_response.text = "Full transcription text without segments."
        mock_response.duration = 10.0

        mock_audio_client = AsyncMock()
        mock_audio_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        mock_clients = MagicMock()
        mock_clients.patched_embedding_client = mock_audio_client

        with patch("config.settings.clients", mock_clients):
            result = await transcribe_media(small_mp3)

        assert len(result["chunks"]) == 1
        assert result["chunks"][0]["text"] == "Full transcription text without segments."
        assert result["chunks"][0]["timestamp_start"] == 0.0

    @pytest.mark.asyncio
    async def test_empty_transcription(self, small_mp3):
        """Test handling of empty transcription."""
        mock_response = MagicMock()
        mock_response.segments = []
        mock_response.text = ""
        mock_response.duration = 0.0

        mock_audio_client = AsyncMock()
        mock_audio_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        mock_clients = MagicMock()
        mock_clients.patched_embedding_client = mock_audio_client

        with patch("config.settings.clients", mock_clients):
            result = await transcribe_media(small_mp3)

        # Should still return valid structure with an empty chunk
        assert len(result["chunks"]) == 1
        assert result["chunks"][0]["text"] == ""

    @pytest.mark.asyncio
    async def test_page_numbers_are_sequential(self, small_mp3):
        """Test that page (chunk) numbers are sequential starting from 1."""
        segments = []
        for i in range(5):
            seg = MagicMock()
            seg.text = "x" * 300  # Each segment is 300 chars
            seg.start = float(i * 10)
            seg.end = float(i * 10 + 10)
            segments.append(seg)

        mock_response = MagicMock()
        mock_response.segments = segments
        mock_response.duration = 50.0

        mock_audio_client = AsyncMock()
        mock_audio_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        mock_clients = MagicMock()
        mock_clients.patched_embedding_client = mock_audio_client

        with patch("config.settings.clients", mock_clients):
            result = await transcribe_media(small_mp3)

        pages = [c["page"] for c in result["chunks"]]
        assert pages == list(range(1, len(pages) + 1))
