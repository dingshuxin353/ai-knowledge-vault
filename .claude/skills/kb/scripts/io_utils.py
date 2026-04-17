#!/usr/bin/env python3
"""Utility helpers for twin-kb ingestion scripts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

SUPPORTED_VIDEO_EXTS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".m4v",
}

SUPPORTED_AUDIO_EXTS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
}


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")


def ensure_dirs(paths: Iterable[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: object | None = None) -> object | None:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_log(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def slugify_filename(text: str, max_len: int = 40) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-_")
    if not cleaned:
        cleaned = "未命名知识"
    return cleaned[:max_len]


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{stderr}")
    return proc


def collect_media_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]

    files: list[Path] = []
    for p in sorted(path.rglob("*")):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in SUPPORTED_VIDEO_EXTS or ext in SUPPORTED_AUDIO_EXTS:
            files.append(p)
    return files


def is_video(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_VIDEO_EXTS


def split_tags(raw: str) -> list[str]:
    if not raw.strip():
        return []
    values = [x.strip() for x in raw.replace("，", ",").split(",")]
    values = [x for x in values if x]
    uniq: list[str] = []
    for v in values:
        if v not in uniq:
            uniq.append(v)
    return uniq
