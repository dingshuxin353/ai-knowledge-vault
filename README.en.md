# ai-knowledge-vault

`ai-knowledge-vault` is a local-first knowledge management template for Obsidian and Claude Code.

It helps you collect source material, turn it into structured Markdown knowledge entries, compile concept pages, and keep the whole vault searchable for both humans and AI agents.

Chinese documentation: [README.md](./README.md)

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

## Do I Need Obsidian Plugins?

No.

This repository works as plain Markdown plus Python scripts, so users do not need to install any Obsidian plugin to get started.

Optional plugins only improve the in-Obsidian experience:

- `Dataview`: useful for the query blocks generated in concept pages
- `Bases`: useful if you want to browse `knowledge/knowledge-base.base`

So the dependency levels are:

- required: no Obsidian plugin
- recommended: Obsidian itself
- optional: `Dataview`, `Bases`

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

Useful folder guides:

- [`knowledge/concepts/README.md`](./knowledge/concepts/README.md)
- [`knowledge/reports/README.md`](./knowledge/reports/README.md)
- [`knowledge/inbox/manual/README.md`](./knowledge/inbox/manual/README.md)
- [`knowledge/inbox/video/README.md`](./knowledge/inbox/video/README.md)

## Documentation

- Chinese guide: [`README.md`](./README.md)
- architecture: [`docs/architecture.md`](./docs/architecture.md)
- installation: [`docs/installation.md`](./docs/installation.md)
- video transcription: [`docs/video-transcription.md`](./docs/video-transcription.md)

## Roadmap

- Improve `/kb process-pending` into a fully scripted workflow
- Add more sample entries and concept heuristics
- Expand docs for non-Claude users and other agent setups

## License

MIT
