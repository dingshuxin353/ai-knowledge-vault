# ai-knowledge-vault

`ai-knowledge-vault` is a local-first knowledge management template for Obsidian and Claude Code.

It helps you collect source material, turn it into structured Markdown knowledge entries, compile concept pages, and keep the whole vault searchable for both humans and AI agents.

Chinese documentation: [README.zh-CN.md](./README.zh-CN.md)

## Features

- Obsidian-friendly knowledge vault structure
- Claude Code skill at `.claude/skills/kb/`
- concept compilation from timeline entries
- query reports and health checks
- manual inbox for pending source files
- optional video or audio transcription via DashScope

## Quick Start

1. Clone this repository:

```bash
git clone https://github.com/dingshuxin353/ai-knowledge-vault.git
cd ai-knowledge-vault
```

2. Open the repository in Obsidian.
3. Review `knowledge/_index.md` and `knowledge/CLAUDE.md`.
4. Install dependencies:

```bash
pip3 install -r requirements.txt
```

5. Use `.claude/skills/kb/` as a local Claude Code skill.
6. Run:

```bash
python3 .claude/skills/kb/scripts/knowledge_ops.py compile
python3 .claude/skills/kb/scripts/knowledge_ops.py health
```

## How It Works

- `knowledge/*.md` stores raw knowledge entries with metadata, summaries, and full source content
- `knowledge/concepts/` is the compiled concept layer for navigation
- `knowledge/reports/` stores reusable search and health-check outputs
- `.claude/skills/kb/` packages the vault workflow as a Claude Code skill

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

- Chinese guide: [`README.zh-CN.md`](./README.zh-CN.md)
- architecture: [`docs/architecture.md`](./docs/architecture.md)
- installation: [`docs/installation.md`](./docs/installation.md)
- video transcription: [`docs/video-transcription.md`](./docs/video-transcription.md)

## Roadmap

- Improve `/kb process-pending` into a fully scripted workflow
- Add more sample entries and concept heuristics
- Expand docs for non-Claude users and other agent setups

## License

MIT
