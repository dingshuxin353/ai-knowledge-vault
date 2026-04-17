#!/usr/bin/env python3
"""Ingest video and audio files into knowledge base entries."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any

from asr_aliyun import DEFAULT_MODEL, transcribe_audio_file
from io_utils import (
    append_log,
    collect_media_files,
    ensure_dirs,
    now_iso,
    read_json,
    run_command,
    sha256_file,
    slugify_filename,
    split_tags,
    today_str,
    write_json,
)
from knowledge_ops import compile_concepts


def _find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "knowledge").is_dir():
            return current
        current = current.parent

    env_root = os.environ.get("KB_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    raise RuntimeError(
        "无法定位仓库根目录。请确保父目录中存在 knowledge/，或设置 KB_ROOT 环境变量。"
    )


REPO_ROOT = _find_repo_root()
SKILL_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
INDEX_PATH = KNOWLEDGE_DIR / "_index.md"
INBOX_DIR = KNOWLEDGE_DIR / "inbox" / "video"
RAW_DIR = INBOX_DIR / "raw"
WORK_DIR = INBOX_DIR / "work"
TRANSCRIPTS_DIR = INBOX_DIR / "transcripts"
LOGS_DIR = INBOX_DIR / "logs"
LOG_FILE = LOGS_DIR / "ingest.log"
PROMPT_FILE = SKILL_DIR / "prompts" / "video_transcript_editing.md"
CONFIG_PATH = SKILL_DIR / "config.json"
CONFIG_LOCAL_PATH = SKILL_DIR / "config.local.json"

RETRY_DELAYS = [5, 15, 45]
DEFAULT_CHUNK_SECONDS = 240


def load_runtime_config() -> dict[str, str]:
    cfg: dict[str, str] = {
        "dashscope_api_key": "",
        "dashscope_base_url": "",
        "asr_model": DEFAULT_MODEL,
    }
    for path in (CONFIG_PATH, CONFIG_LOCAL_PATH):
        if not path.exists():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"配置文件解析失败: {path} ({exc})") from exc
        if not isinstance(raw, dict):
            raise RuntimeError(f"配置文件格式错误（应为对象）: {path}")
        for key in cfg:
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                cfg[key] = value.strip()
    return cfg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="视频或音频素材入库：转写、轻度校对、写入 knowledge/ 并更新索引。",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(RAW_DIR),
        help="视频/音频文件路径或目录路径，默认使用 knowledge/inbox/video/raw/",
    )
    parser.add_argument("--source-url", default="", help="可选：原始内容链接")
    parser.add_argument("--title", default="", help="可选：覆盖自动标题")
    parser.add_argument("--tags", default="", help="可选：逗号分隔标签")
    parser.add_argument(
        "--chunk-seconds",
        type=int,
        default=DEFAULT_CHUNK_SECONDS,
        help=f"音频切片秒数，默认 {DEFAULT_CHUNK_SECONDS}",
    )
    parser.add_argument(
        "--model",
        default="",
        help=f"ASR 模型名，优先级：参数 > 环境变量 > config > 默认({DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="可选：DashScope API base URL（优先级：参数 > 环境变量 > config > 默认）",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="可选：DashScope API Key（优先级：参数 > 环境变量 > config）",
    )
    return parser.parse_args()


def probe_duration_seconds(path: Path) -> float:
    proc = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    raw = (proc.stdout or "").strip()
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"无法读取媒体时长: {path}") from exc


def normalize_to_audio(input_path: Path, output_audio: Path) -> None:
    # 统一为单声道 16k mp3，便于切片和提交 ASR。
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "64k",
            str(output_audio),
        ]
    )


def split_audio_chunks(audio_path: Path, chunk_dir: Path, chunk_seconds: int) -> list[Path]:
    duration = probe_duration_seconds(audio_path)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    if duration <= float(chunk_seconds) + 1:
        chunk = chunk_dir / "chunk_0000.mp3"
        shutil.copy2(audio_path, chunk)
        return [chunk]

    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(audio_path),
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-reset_timestamps",
            "1",
            "-c",
            "copy",
            str(chunk_dir / "chunk_%04d.mp3"),
        ]
    )
    chunks = sorted(chunk_dir.glob("chunk_*.mp3"))
    if not chunks:
        raise RuntimeError("音频切片失败，未生成分片文件")
    return chunks


def transcribe_with_retry(
    chunk_path: Path,
    *,
    model: str,
    base_url: str,
    api_key: str,
) -> tuple[str, str]:
    last_error: Exception | None = None
    for attempt, delay in enumerate([0] + RETRY_DELAYS, start=1):
        if delay:
            time.sleep(delay)
        try:
            resp = transcribe_audio_file(
                chunk_path,
                api_key=api_key,
                model=model,
                base_url=base_url or None,
                language="zh",
                enable_itn=False,
            )
            return resp["text"], resp.get("request_id", "")
        except Exception as exc:
            last_error = exc
            if attempt >= 1 + len(RETRY_DELAYS):
                break
    raise RuntimeError(f"分片转写失败: {chunk_path.name} ({last_error})")


def light_edit_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]*([，。！？；：])[ ]*", r"\1", text)
    text = text.strip()

    if not text:
        return ""

    # 按句号类标点做简单段落化，避免整段无断句。
    sentences = re.split(r"(?<=[。！？!?])\s*", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return text

    paras: list[str] = []
    for i in range(0, len(sentences), 3):
        paras.append("".join(sentences[i : i + 3]))
    return "\n\n".join(paras)


def extract_core_points_placeholder() -> str:
    # 按用户要求：脚本阶段不调用第三方模型，核心观点由当前 Agent 在脚本后补写。
    return ""


def detect_existing_tags(index_path: Path) -> set[str]:
    if not index_path.exists():
        return set()
    text = index_path.read_text(encoding="utf-8")
    return {m.group(1).strip() for m in re.finditer(r"^###\s+(.+)$", text, flags=re.MULTILINE)}


def infer_tags(clean_text: str, filename: str, user_tags: list[str], existing_tags: set[str]) -> list[str]:
    if user_tags:
        return user_tags[:5]

    candidates = ["视频转写", "AI学习"]
    name_and_text = f"{filename}\n{clean_text}".lower()
    keyword_map = {
        "prompt": "Prompt Engineering",
        "提示词": "Prompt Engineering",
        "agent": "Agent",
        "智能体": "Agent",
        "rag": "RAG",
        "知识库": "Knowledge Base",
        "工作流": "Workflow",
        "自动化": "Automation",
    }
    for keyword, tag in keyword_map.items():
        if keyword in name_and_text and tag not in candidates:
            candidates.append(tag)

    # 尽量复用索引中已有标签，大小写/空格宽松匹配。
    normalized_existing = {t.lower().replace(" ", ""): t for t in existing_tags}
    reused: list[str] = []
    for tag in candidates:
        key = tag.lower().replace(" ", "")
        reused.append(normalized_existing.get(key, tag))

    uniq: list[str] = []
    for tag in reused:
        if tag not in uniq:
            uniq.append(tag)
    return uniq[:5]


def derive_title(explicit_title: str, source_stem: str, clean_text: str) -> str:
    if explicit_title.strip():
        return explicit_title.strip()
    first_sentence = re.split(r"[。！？!?]", clean_text.strip())[0].strip()
    if first_sentence:
        return first_sentence[:22]
    return source_stem[:22] if source_stem else "视频知识摘录"


def make_entry_filename(date_str: str, title: str, existing_files: set[str]) -> str:
    base = f"{date_str}-{slugify_filename(title)}.md"
    if base not in existing_files:
        return base
    idx = 2
    while True:
        cand = f"{date_str}-{slugify_filename(title)}-{idx}.md"
        if cand not in existing_files:
            return cand
        idx += 1


def format_entry_markdown(
    *,
    date_str: str,
    source: str,
    source_url: str,
    tags: list[str],
    title: str,
    core_points: str,
    clean_text: str,
) -> str:
    tags_block = "\n".join(f"  - {tag}" for tag in tags)
    source_url_value = source_url.strip()
    quote_lines = []
    for line in clean_text.splitlines():
        quote_lines.append("> " + line if line.strip() else ">")
    quoted = "\n".join(quote_lines).strip() or "> （空）"

    return (
        "---\n"
        f"date: {date_str}\n"
        f"source: {source}\n"
        "source_type: video\n"
        f"source_url: \"{source_url_value}\"\n"
        "tags:\n"
        f"{tags_block}\n"
        "confidence: processed\n"
        "---\n\n"
        f"# {title}\n\n"
        "## 核心观点\n"
        f"{core_points}\n\n"
        "## 我的思考\n"
        "- 待补充。\n\n"
        "## 原始内容\n"
        f"{quoted}\n"
    )


def rebuild_index() -> None:
    compile_concepts(write_related=True)


def load_processed_hashes() -> set[str]:
    hashes: set[str] = set()
    for meta_file in TRANSCRIPTS_DIR.glob("*.meta.json"):
        meta = read_json(meta_file, default={}) or {}
        if not isinstance(meta, dict):
            continue
        if meta.get("status") == "success" and isinstance(meta.get("source_sha256"), str):
            hashes.add(meta["source_sha256"])
    return hashes


def process_media_file(
    media_file: Path,
    *,
    source_url: str,
    explicit_title: str,
    explicit_tags: list[str],
    chunk_seconds: int,
    model: str,
    base_url: str,
    api_key: str,
    processed_hashes: set[str],
) -> tuple[bool, str]:
    source_sha = sha256_file(media_file)
    if source_sha in processed_hashes:
        return True, f"跳过重复文件: {media_file.name}"

    ts = time.strftime("%Y%m%dT%H%M%S")
    job_id = f"{ts}-{source_sha[:8]}"
    job_work = WORK_DIR / job_id
    chunk_dir = job_work / "chunks"
    normalized_audio = job_work / "normalized.mp3"
    meta_path = TRANSCRIPTS_DIR / f"{job_id}.meta.json"
    raw_path = TRANSCRIPTS_DIR / f"{job_id}.raw.txt"
    clean_path = TRANSCRIPTS_DIR / f"{job_id}.clean.txt"

    ensure_dirs([job_work, chunk_dir, TRANSCRIPTS_DIR, LOGS_DIR])
    start_at = now_iso()
    meta: dict[str, Any] = {
        "job_id": job_id,
        "source_file": str(media_file),
        "source_sha256": source_sha,
        "duration_sec": 0,
        "chunks": [],
        "vendor": "aliyun",
        "model": model,
        "core_points_status": "pending_agent",
        "status": "running",
        "error": None,
        "created_at": start_at,
        "updated_at": start_at,
        "prompt_file": str(PROMPT_FILE),
    }
    write_json(meta_path, meta)

    try:
        normalize_to_audio(media_file, normalized_audio)
        media_duration = probe_duration_seconds(media_file)
        meta["duration_sec"] = round(media_duration, 2)

        chunk_files = split_audio_chunks(normalized_audio, chunk_dir, chunk_seconds)
        transcripts: list[str] = []

        for idx, chunk in enumerate(chunk_files):
            chunk_duration = round(probe_duration_seconds(chunk), 2)
            start_sec = round(idx * chunk_seconds, 2)
            end_sec = round(start_sec + chunk_duration, 2)
            text, request_id = transcribe_with_retry(
                chunk,
                model=model,
                base_url=base_url,
                api_key=api_key,
            )
            transcripts.append(text.strip())
            meta["chunks"].append(
                {
                    "index": idx,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "audio_file": str(chunk),
                    "char_count": len(text.strip()),
                    "request_id": request_id,
                    "status": "success",
                }
            )

        raw_text = "\n\n".join(t for t in transcripts if t)
        raw_path.write_text(raw_text.strip() + "\n", encoding="utf-8")
        clean_text = light_edit_text(raw_text)
        clean_path.write_text(clean_text.strip() + "\n", encoding="utf-8")

        title = derive_title(explicit_title, media_file.stem, clean_text)
        existing_tags = detect_existing_tags(INDEX_PATH)
        tags = infer_tags(clean_text, media_file.name, explicit_tags, existing_tags)
        core_points = extract_core_points_placeholder()

        existing_files = {p.name for p in KNOWLEDGE_DIR.glob("*.md")}
        date_str = today_str()
        source = f"视频/音频素材/{media_file.name}"
        entry_name = make_entry_filename(date_str, title, existing_files)
        entry_path = KNOWLEDGE_DIR / entry_name
        entry_content = format_entry_markdown(
            date_str=date_str,
            source=source,
            source_url=source_url,
            tags=tags,
            title=title,
            core_points=core_points,
            clean_text=clean_text,
        )
        entry_path.write_text(entry_content, encoding="utf-8")
        rebuild_index()

        meta["status"] = "success"
        meta["entry_file"] = str(entry_path.relative_to(REPO_ROOT))
        meta["raw_text_file"] = str(raw_path.relative_to(REPO_ROOT))
        meta["clean_text_file"] = str(clean_path.relative_to(REPO_ROOT))
        meta["core_points_status"] = "pending_agent"
        meta["updated_at"] = now_iso()
        write_json(meta_path, meta)
        processed_hashes.add(source_sha)
        return True, f"完成入库: {entry_path.relative_to(REPO_ROOT)}"
    except Exception as exc:  # noqa: BLE001
        meta["status"] = "failed"
        meta["error"] = str(exc)
        meta["updated_at"] = now_iso()
        write_json(meta_path, meta)
        return False, f"处理失败 {media_file.name}: {exc}"


def main() -> int:
    args = parse_args()
    cfg = load_runtime_config()
    ensure_dirs([RAW_DIR, WORK_DIR, TRANSCRIPTS_DIR, LOGS_DIR])

    api_key = args.api_key.strip() or os.getenv("DASHSCOPE_API_KEY", "").strip() or cfg["dashscope_api_key"]
    base_url = (
        args.base_url.strip()
        or os.getenv("DASHSCOPE_BASE_URL", "").strip()
        or cfg["dashscope_base_url"]
    )
    model = args.model.strip() or os.getenv("ALIYUN_ASR_MODEL", "").strip() or cfg["asr_model"] or DEFAULT_MODEL
    if not api_key:
        raise SystemExit(
            "未配置 DashScope API Key。请使用以下任一方式："
            "--api-key 参数 / 环境变量 DASHSCOPE_API_KEY / "
            ".claude/skills/kb/config.local.json"
        )

    target = Path(args.path).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    if not target.exists():
        raise SystemExit(f"路径不存在: {target}")

    media_files = collect_media_files(target)
    if not media_files:
        raise SystemExit(f"未找到可处理的视频或音频文件: {target}")

    explicit_tags = split_tags(args.tags)
    processed_hashes = load_processed_hashes()

    print(f"发现素材 {len(media_files)} 个，开始处理...")
    success_count = 0
    failed_count = 0
    for media_file in media_files:
        ok, message = process_media_file(
            media_file,
            source_url=args.source_url,
            explicit_title=args.title,
            explicit_tags=explicit_tags,
            chunk_seconds=args.chunk_seconds,
            model=model,
            base_url=base_url,
            api_key=api_key,
            processed_hashes=processed_hashes,
        )
        print(message)
        append_log(LOG_FILE, f"[{now_iso()}] {'OK' if ok else 'FAIL'} {message}")
        if ok:
            success_count += 1
        else:
            failed_count += 1

    print(f"\n处理完成：成功 {success_count}，失败 {failed_count}")
    if success_count:
        print("提示：本脚本不会自动生成“核心观点”，请由当前Agent在入库后补写并重建索引。")
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
