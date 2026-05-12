#!/usr/bin/env python3
"""
PDF to Markdown converter using MinerU cloud API.

Usage:
    python pdf_to_md.py --input-dir input/ --output-dir input/

Flow (3 steps per file):
    1. POST /api/v4/file-urls/batch  → get batch_id + OSS upload URL
    2. PUT {oss_url}                  → upload PDF binary to Alibaba Cloud OSS
    3. GET  /api/v4/extract-results/batch/{batch_id}  → poll until done, download ZIP, extract .md
"""

import argparse
import io
import os
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

import requests

MINERU_BASE = "https://mineru.net"

# Fix Windows console encoding for Chinese filenames
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def load_api_key(cli_key: str | None) -> str:
    if cli_key:
        return cli_key
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("MINERU_API_KEY="):
                return line.split("=", 1)[1].strip()
    print("ERROR: No API key found. Use --api-key or set MINERU_API_KEY in .env", file=sys.stderr)
    sys.exit(2)


def submit_task(api_key: str, filename: str) -> tuple[str, str]:
    """Submit a batch task, return (batch_id, oss_upload_url)."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "layout": True,
        "language": "ch",
        "model_version": "pipeline",
        "files": [
            {
                "name": filename,
                "is_ocr": True,
                "enable_table": True,
            }
        ],
    }
    resp = requests.post(f"{MINERU_BASE}/api/v4/file-urls/batch", json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    batch_id = data["data"]["batch_id"]
    upload_url = data["data"]["file_urls"][0]
    return batch_id, upload_url


def upload_file(upload_url: str, file_path: Path) -> None:
    """Upload file binary to the presigned OSS URL."""
    with open(file_path, "rb") as f:
        resp = requests.put(upload_url, data=f)
    resp.raise_for_status()


def poll_result(api_key: str, batch_id: str, interval: int, timeout: int) -> str:
    """Poll until task is done, return the ZIP download URL."""
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise TimeoutError(f"Polling timed out after {timeout}s for batch {batch_id}")

        resp = requests.get(
            f"{MINERU_BASE}/api/v4/extract-results/batch/{batch_id}", headers=headers
        )
        resp.raise_for_status()
        data = resp.json()

        extract_result = data.get("data", {}).get("extract_result", [])
        if extract_result:
            item = extract_result[0]
            state = item.get("state", "unknown")
            if state == "done":
                url = item.get("full_zip_url") or item.get("download_url") or item.get("url", "")
                if not url:
                    raise RuntimeError(f"Task done but no download URL: {item}")
                return url
            elif state in ("failed", "error"):
                err_msg = item.get("err_msg", "")
                raise RuntimeError(f"Task failed: state={state}, msg={err_msg}")

            print(f"  ... polling ({state}), {int(elapsed)}s elapsed", file=sys.stderr)
        else:
            print(f"  ... polling (no result yet), {int(elapsed)}s elapsed", file=sys.stderr)

        time.sleep(interval)


def download_and_extract_md(zip_url: str) -> str:
    """Download ZIP from URL and extract the first .md content."""
    resp = requests.get(zip_url)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        md_files = [n for n in zf.namelist() if n.endswith(".md")]
        if not md_files:
            raise RuntimeError(f"No .md file found in ZIP. Contents: {zf.namelist()}")
        return zf.read(md_files[0]).decode("utf-8")


def format_output(stem: str, pdf_rel_path: str, content: str) -> str:
    """Wrap extracted content with metadata header."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"# {stem}\n\n"
        f"> 来源：{pdf_rel_path}\n"
        f"> 转换时间：{now}\n"
        f"> 转换方式：MinerU API (OCR + 表格识别)\n\n"
        f"## 文档内容\n\n{content}"
    )


def process_file(api_key: str, pdf_path: Path, output_dir: Path, interval: int, timeout: int) -> bool:
    """Process a single PDF. Returns True on success."""
    stem = pdf_path.stem
    out_path = output_dir / f"{stem}_converted.md"

    print(f"Converting: {pdf_path.name}")
    try:
        batch_id, upload_url = submit_task(api_key, pdf_path.name)
        print(f"  Submitted batch {batch_id}, uploading file...")
        upload_file(upload_url, pdf_path)
        print(f"  Uploaded, polling for result...")
        zip_url = poll_result(api_key, batch_id, interval, timeout)
        print(f"  Done, downloading result...")
        md_content = download_and_extract_md(zip_url)

        output = format_output(stem, f"input/{pdf_path.name}", md_content)
        out_path.write_text(output, encoding="utf-8")
        print(f"  -> {out_path.name}")
        return True
    except Exception as e:
        print(f"  FAILED: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert PDFs to Markdown using MinerU API")
    parser.add_argument("--input-dir", default="input", help="Directory containing PDF files")
    parser.add_argument("--output-dir", default="input", help="Directory for output .md files")
    parser.add_argument("--api-key", default=None, help="MinerU API key (or set MINERU_API_KEY in .env)")
    parser.add_argument("--poll-interval", type=int, default=10, help="Polling interval in seconds")
    parser.add_argument("--timeout", type=int, default=300, help="Per-file timeout in seconds")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(2)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(input_dir.glob("*.pdf"))
    pdfs = [p for p in pdfs if not (output_dir / f"{p.stem}_converted.md").exists()]

    if not pdfs:
        print("No PDFs to convert (all already converted or no PDFs found).")
        sys.exit(0)

    print(f"Found {len(pdfs)} PDF(s) to convert:")
    for p in pdfs:
        print(f"  - {p.name}")
    print()

    api_key = load_api_key(args.api_key)

    success, fail = 0, 0
    for pdf in pdfs:
        if process_file(api_key, pdf, output_dir, args.poll_interval, args.timeout):
            success += 1
        else:
            fail += 1

    print(f"\nDone: {success} succeeded, {fail} failed.")
    if fail == len(pdfs):
        sys.exit(2)
    elif fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
