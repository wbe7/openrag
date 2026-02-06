#!/usr/bin/env python3
"""
Utility to sync embedded component code inside Langflow JSON files.

Given a Python source file (e.g. the OpenSearch component implementation) and
a target selector, this script updates every flow definition in ``./flows`` so
that the component's ``template.code.value`` matches the supplied file.

Example:
    python scripts/update_flow_components.py \\
        --code-file flows/components/opensearch_multimodel.py \\
        --display-name "OpenSearch (Multi-Model)"
"""

from __future__ import annotations

import argparse
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Iterable, Any


def load_code(source_path: Path) -> str:
    try:
        return source_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"[error] code file not found: {source_path}") from exc


def should_update_component(node: dict, *, display_name: str | None, metadata_module: str | None) -> bool:
    node_data = node.get("data", {})
    component = node_data.get("node", {})

    if display_name:
        node_display_name = component.get("display_name")
        if node_display_name != display_name:
            return False

    if metadata_module:
        metadata = component.get("metadata", {})
        module_name = metadata.get("module")
        if module_name != metadata_module:
            return False

    template = component.get("template", {})
    code_entry = template.get("code")
    return isinstance(code_entry, dict) and "value" in code_entry


def sort_template(template: dict) -> dict:
    """Sort keys of the template and its nested dictionaries recursively (1 level deep)."""
    sorted_template = {}
    for key in sorted(template.keys()):
        val = template[key]
        if isinstance(val, dict):
            # Sort keys of the value dict
            sorted_template[key] = {k: val[k] for k in sorted(val.keys())}
        else:
            sorted_template[key] = val
    return sorted_template


def is_langflow_running(url: str = "http://localhost:7860") -> bool:
    try:
        # Checking health endpoint or just root
        with urllib.request.urlopen(f"{url}/health", timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
        return False


def update_component_via_api(frontend_node: dict, code: str, url: str = "http://localhost:7860", api_key: str | None = None) -> dict | None:
    endpoint = f"{url}/api/v1/custom_component"
    
    # Update the code in the frontend_node before sending it to the API
    # We need to make sure we are working on a copy or modifying strictly what's needed
    # But for the payload, we need the updated state.
    frontend_node["template"]["code"]["value"] = code

    # Construct payload
    payload = {
        "code": code,
        "frontend_node": frontend_node,
    }
    
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                resp_data = json.load(response)
                
                if "data" in resp_data and isinstance(resp_data["data"], dict):
                    data_obj = resp_data["data"]
                    
                    # Try to find template in data
                    if "node" in data_obj:
                        return data_obj["node"].get("template")
                    if "template" in data_obj:
                        return data_obj.get("template")
                
                # Fallback
                return resp_data.get("template")
    except urllib.error.HTTPError as e:
        print(f"[warning] API update failed: {e}")
        try:
            error_body = e.read().decode("utf-8")
            print(f"    Server response: {error_body}")
        except Exception:
            pass
        return None
    except urllib.error.URLError as e:
        print(f"[warning] API update failed: {e}")
        return None
    
    return None


def update_flow(flow_path: Path, code: str, *, display_name: str | None, metadata_module: str | None, dry_run: bool, langflow_url: str | None, api_key: str | None) -> bool:
    with flow_path.open(encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"[error] failed to parse {flow_path}: {exc}") from exc

    changed = False

    for node in data.get("data", {}).get("nodes", []):
        if not should_update_component(node, display_name=display_name, metadata_module=metadata_module):
            continue
        
    for node in data.get("data", {}).get("nodes", []):
        if not should_update_component(node, display_name=display_name, metadata_module=metadata_module):
            continue

        template = node["data"]["node"]["template"]
        current_code = template["code"]["value"]
        
        # Check if update is needed
        # We always check if we can update via API if URL is provided, because the compiled template might be different
        # even if the source code string matches (e.g. dynamic fields)
        
        updated_via_api = False
        should_process = False
        
        if current_code != code:
            should_process = True
        elif langflow_url:
             should_process = True
             
        if should_process:
            if dry_run:
                changed = True
            else:
                if langflow_url:
                    print(f"  - Updating component via Langflow API at {langflow_url}...")
                    # We pass the whole frontend node (node['data']['node'])
                    frontend_node = node["data"]["node"]
                    new_template = update_component_via_api(frontend_node, code, url=langflow_url, api_key=api_key)
                    if new_template:
                        # The user said "return you the component json that you need to replace on the file"
                        # The API returns data which has "template".
                        # We replace the whole template object.
                        node["data"]["node"]["template"] = sort_template(new_template)
                        updated_via_api = True
                        print("    -> API Update successful. Template updated.")
                    else:
                        print("    -> API Update failed/returned no template. Falling back to local string replacement.")

                if not updated_via_api:
                    template["code"]["value"] = code
                    # Also sort the existing template if we modified it locally
                    node["data"]["node"]["template"] = sort_template(template)
                
                changed = True

    if changed and not dry_run:
        try:
            content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
            flow_path.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"[error] Failed to write to {flow_path}: {e}")

    return changed


def iter_flow_files(flows_dir: Path) -> Iterable[Path]:
    for path in sorted(flows_dir.glob("*.json")):
        if path.is_file():
            yield path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update embedded component code in Langflow JSON files.")
    parser.add_argument("--code-file", required=True, type=Path, help="Path to the Python file containing the component code.")
    parser.add_argument("--flows-dir", type=Path, default=Path("flows"), help="Directory containing Langflow JSON files.")
    parser.add_argument("--display-name", help="Component display_name to match (e.g. 'OpenSearch (Multi-Model)').")
    parser.add_argument("--metadata-module", help="Component metadata.module value to match.")
    parser.add_argument("--dry-run", action="store_true", help="Report which files would change without modifying them.")
    parser.add_argument("--langflow-url", default="http://localhost:7860", help="URL of running Langflow instance to use for component updates.")
    parser.add_argument("--api-key", help="API Key for Langflow authentication.")
    parser.add_argument("--skip-api", action="store_true", help="Skip checking/using Langflow API even if available.")

    args = parser.parse_args()

    if not args.display_name and not args.metadata_module:
        parser.error("At least one of --display-name or --metadata-module must be provided.")

    return args


def main() -> None:
    args = parse_args()

    flows_dir: Path = args.flows_dir
    if not flows_dir.exists():
        raise SystemExit(f"[error] flows directory not found: {flows_dir}")

    code = load_code(args.code_file)
    
    # Check Langflow status
    langflow_url = None
    if not args.skip_api:
        if is_langflow_running(args.langflow_url):
            print(f"[info] Langflow detected at {args.langflow_url}. Will use API for updates.")
            langflow_url = args.langflow_url
        else:
            print(f"[info] Langflow not detected at {args.langflow_url}. Performing local string updates only.")

    updated_files = []
    for flow_path in iter_flow_files(flows_dir):
        changed = update_flow(
            flow_path,
            code,
            display_name=args.display_name,
            metadata_module=args.metadata_module,
            dry_run=args.dry_run,
            langflow_url=langflow_url,
            api_key=args.api_key
        )
        if changed:
            updated_files.append(flow_path)

    if args.dry_run:
        if updated_files:
            print("[dry-run] files that would be updated:")
            for path in updated_files:
                print(f"  - {path}")
        else:
            print("[dry-run] no files would change.")
    else:
        if updated_files:
            print("Updated component code in:")
            for path in updated_files:
                print(f"  - {path}")
        else:
            print("No updates were necessary.")


if __name__ == "__main__":
    main()
