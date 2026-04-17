#!/usr/bin/env python3
"""Aliyun ASR wrapper for qwen3-asr-flash."""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
DEFAULT_MODEL = "qwen3-asr-flash"


def _guess_audio_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime and mime.startswith("audio/"):
        return mime
    if path.suffix.lower() == ".m4a":
        return "audio/mp4"
    if path.suffix.lower() == ".wav":
        return "audio/wav"
    return "audio/mpeg"


def _response_to_dict(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response
    if hasattr(response, "to_dict"):
        try:
            return response.to_dict()
        except Exception:
            pass
    if hasattr(response, "__dict__"):
        data = {k: v for k, v in vars(response).items() if not k.startswith("_")}
        if data:
            return data
    return {"raw": str(response)}


def _extract_text(data: dict[str, Any]) -> str:
    output = data.get("output", {})
    choices = output.get("choices", [])
    texts: list[str] = []

    for choice in choices:
        message = choice.get("message", {})
        content = message.get("content", [])
        if isinstance(content, str):
            texts.append(content)
            continue
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    texts.append(item["text"])

    if texts:
        return "\n".join(x.strip() for x in texts if x and x.strip()).strip()

    # Fallback for schema changes
    fallback: list[str] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"text", "transcript", "asr_result"} and isinstance(value, str):
                    fallback.append(value)
                else:
                    _walk(value)
            return
        if isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(data)
    uniq: list[str] = []
    for text in fallback:
        t = text.strip()
        if t and t not in uniq:
            uniq.append(t)
    return "\n".join(uniq).strip()


def transcribe_audio_file(
    audio_path: Path,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
    language: str = "zh",
    enable_itn: bool = False,
) -> dict[str, Any]:
    """Transcribe a local audio file via DashScope multimodal conversation API."""
    try:
        import dashscope
    except ImportError as exc:
        raise RuntimeError("缺少依赖 dashscope，请先安装: pip3 install dashscope") from exc

    token = api_key or os.getenv("DASHSCOPE_API_KEY")
    if not token:
        raise RuntimeError("未设置 DASHSCOPE_API_KEY")

    dashscope.base_http_api_url = base_url or os.getenv("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL)

    mime = _guess_audio_mime(audio_path)
    data_b64 = base64.b64encode(audio_path.read_bytes()).decode("utf-8")
    data_uri = f"data:{mime};base64,{data_b64}"

    messages = [
        {"role": "system", "content": [{"text": ""}]},
        {"role": "user", "content": [{"audio": data_uri}]},
    ]
    response = dashscope.MultiModalConversation.call(
        api_key=token,
        model=model,
        messages=messages,
        result_format="message",
        asr_options={
            "language": language,
            "enable_itn": enable_itn,
        },
    )

    data = _response_to_dict(response)
    status_code = getattr(response, "status_code", None) or data.get("status_code")
    if isinstance(status_code, int) and status_code >= 400:
        raise RuntimeError(f"ASR 调用失败，status_code={status_code}, response={data}")

    code = data.get("code")
    if code:
        msg = data.get("message") or data.get("error_message") or "未知错误"
        raise RuntimeError(f"ASR 返回错误 code={code}, message={msg}")

    text = _extract_text(data)
    if not text:
        raise RuntimeError("ASR 返回空文本")

    return {
        "text": text,
        "request_id": data.get("request_id") or getattr(response, "request_id", ""),
        "status_code": status_code or 200,
        "raw": data,
    }
