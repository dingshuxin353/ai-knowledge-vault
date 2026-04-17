# ai-knowledge-vault

`ai-knowledge-vault` is a local-first knowledge management template for Obsidian and Claude Code.

It helps you collect source material, turn it into structured Markdown knowledge entries, compile concept pages, and keep the whole vault searchable for both humans and AI agents.

## Features

- Obsidian-friendly knowledge vault structure
- Claude Code skill at `.claude/skills/kb/`
- concept compilation from timeline entries
- query reports and health checks
- manual inbox for pending source files
- optional video or audio transcription via DashScope

## Quick Start

1. Clone this repository.
2. Open the repository in Obsidian.
3. Review `knowledge/_index.md` and `knowledge/CLAUDE.md`.
4. Use `.claude/skills/kb/` as a local Claude Code skill.
5. Run:

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py compile
python3 .claude/skills/kb/scripts/knowledge_ops.py health
```

## Core Commands

- `/kb add`
- `/kb find`
- `/kb process-pending`
- `/kb compile`
- `/kb health`
- `/kb tidy`
- `/kb add-video`

## Project Layout

```text
knowledge/
  _index.md
  concepts/
  reports/
  inbox/
    manual/
    video/
.claude/skills/kb/
docs/
```

## Documentation

- Chinese guide: `README.zh-CN.md`
- architecture: `docs/architecture.md`
- installation: `docs/installation.md`
- video transcription: `docs/video-transcription.md`

## License

MIT
