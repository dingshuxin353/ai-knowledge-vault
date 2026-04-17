# Installation

## Requirements

- Python 3.8+
- `PyYAML`
- Obsidian for the best browsing experience

Optional:

- `dashscope`
- `ffmpeg`
- DashScope API key for video transcription

## Setup

1. Clone the repository.
2. Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

3. Open the repository in Obsidian.
4. If you want to use the skill from Claude Code, copy or symlink `.claude/skills/kb/` into your skills directory.

## Verify

Run:

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py compile
python3 .claude/skills/kb/scripts/knowledge_ops.py health
```

If the repo root cannot be detected automatically, set:

```bash
export KB_ROOT=/absolute/path/to/ai-knowledge-vault
```

## Config

For local API keys, create:

```bash
cp .claude/skills/kb/config.example.json .claude/skills/kb/config.local.json
```

Then fill in your values.

## Troubleshooting

- If concept pages are empty, add more entries and run `compile` again.
- If `dashscope` import fails, install it with `pip3 install dashscope`.
- If video ingestion fails before transcription starts, verify `ffmpeg` and `ffprobe` are installed.
