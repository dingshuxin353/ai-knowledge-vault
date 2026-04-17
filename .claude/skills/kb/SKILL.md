---
name: kb
description: Manage an Obsidian-based AI knowledge vault with /kb add/find/process-pending/compile/health/tidy/add-video.
---

# /kb - AI Knowledge Vault

Manage the `knowledge/` directory in this repository as a reusable AI knowledge vault.

## Triggers

- `/kb process-pending`
- `/kb add [content or URL]`
- `/kb find [query]`
- `/kb add-video [file-or-directory]`
- `/kb compile`
- `/kb health`
- `/kb tidy`

## Guardrails

- Do not scan every `knowledge/*.md` file by default; start from `knowledge/_index.md`
- Store all knowledge entries under `knowledge/`
- Keep the original source content in full under `## 原始内容`
- Reuse existing tags and concept names when possible
- Prefer local config files for API keys; use environment variables as fallback
- Treat `knowledge/concepts/` as the primary navigation layer and `knowledge/reports/` as reusable query output

## Workflows

### 1) `/kb process-pending`

Process files in `knowledge/inbox/manual/pending/` and turn them into structured entries.

Expected behavior:
1. Read `knowledge/_index.md` first for existing tags and concepts
2. For each pending Markdown file, extract metadata, summarize 1-3 key points, optionally add `我的思考`
3. Write a normalized entry to `knowledge/YYYY-MM-DD-title.md`
4. Update `knowledge/_index.md`
5. Move the source file to `knowledge/inbox/manual/processed/` or `review/` when uncertain

This workflow is handled directly by the agent, not by a Python CLI command.

### 2) `/kb add`

Add a single piece of knowledge from text, notes, or a URL.

Expected behavior:
1. Detect source type
2. Read `knowledge/_index.md` for nearby tags and concepts
3. Write a structured entry with frontmatter, `核心观点`, optional `我的思考`, and full `原始内容`
4. Update `knowledge/_index.md`

### 3) `/kb find`

Search the knowledge vault and optionally generate a reusable report.

Command:

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py find "context engineering"
```

Output should prioritize:
- matching concepts
- matching entries
- key takeaways
- suggested follow-up reading

### 4) `/kb add-video`

Transcribe local video or audio files, lightly clean the transcript, and create knowledge entries.

Prerequisites:
- `pip3 install dashscope`
- `ffmpeg` and `ffprobe` available on the machine
- Copy `.claude/skills/kb/config.example.json` to `.claude/skills/kb/config.local.json` and fill in `dashscope_api_key`
  or set `DASHSCOPE_API_KEY`

Default input directory:
- `knowledge/inbox/video/raw/`

Command:

```bash
python3 .claude/skills/kb/scripts/video_ingest.py [path]
```

Outputs:
- `knowledge/inbox/video/transcripts/*.raw.txt`
- `knowledge/inbox/video/transcripts/*.clean.txt`
- `knowledge/inbox/video/transcripts/*.meta.json`
- `knowledge/inbox/video/logs/ingest.log`
- new knowledge entry files under `knowledge/`

Quality rules:
- Only do light transcript cleanup
- Do not invent facts
- Leave `核心观点` blank for the current agent to fill in later

### 5) `/kb compile`

Compile timeline entries into concept pages, related links, index, and Bases view.

Command:

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py compile
```

### 6) `/kb health`

Generate a health report for isolated entries, concept gaps, stale raw files, and report coverage.

Command:

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py health
```

### 7) `/kb tidy`

Normalize tags and rebuild concepts, index, health report, and Bases view.

Command:

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py tidy
```

## Troubleshooting

- If `find`, `compile`, or `health` fail to locate the repo root, set `KB_ROOT=/absolute/path/to/repo`
- If `add-video` fails, verify `dashscope` installation, API key config, and `ffmpeg` availability
