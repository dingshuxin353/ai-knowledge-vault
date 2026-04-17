# Knowledge Directory Guide

This directory is the core of the knowledge vault, designed for Obsidian + Claude Code workflows.

## Structure

- `_index.md` - main navigation entry
- `concepts/` - compiled concept pages
- `reports/` - saved query and health reports
- `inbox/manual/` - manually collected source material
- `inbox/video/` - raw media files, transcripts, logs, and temporary work files
- `*.md` - knowledge entries in `YYYY-MM-DD-title.md` format

## How To Work

### Add knowledge

Use `/kb add [content-or-url]`

### Process pending files

Use `/kb process-pending`

### Search

Use `/kb find [query]`

### Compile concepts

Use `/kb compile`

### Run health checks

Use `/kb health`

### Ingest video or audio

Use `/kb add-video [file-or-directory]`

For detailed behavior and commands, see `.claude/skills/kb/SKILL.md`.
