# Video Transcription

## What It Does

The optional video ingestion workflow turns local video or audio files into:

- cleaned transcript artifacts
- a new knowledge entry
- refreshed index and concept pages

## Supported Inputs

- `.mp4`
- `.mov`
- `.mkv`
- `.m4a`
- `.mp3`
- `.wav`

## Dependencies

- `ffmpeg`
- `ffprobe`
- `dashscope`
- DashScope API key

## Config

Copy the example config:

```bash
cp .claude/skills/kb/config.example.json .claude/skills/kb/config.local.json
```

Fill in:

```json
{
  "dashscope_api_key": "",
  "dashscope_base_url": "https://dashscope.aliyuncs.com/api/v1",
  "asr_model": "qwen3-asr-flash"
}
```

## Usage

Put files in `knowledge/inbox/video/raw/`, then run:

```bash
python3 .claude/skills/kb/scripts/video_ingest.py
```

Or pass a file or directory path explicitly:

```bash
python3 .claude/skills/kb/scripts/video_ingest.py path/to/media
```

## Output

- `knowledge/inbox/video/transcripts/*.raw.txt`
- `knowledge/inbox/video/transcripts/*.clean.txt`
- `knowledge/inbox/video/transcripts/*.meta.json`
- `knowledge/inbox/video/logs/ingest.log`

The script intentionally leaves `核心观点` empty so the current agent can fill it in later.
