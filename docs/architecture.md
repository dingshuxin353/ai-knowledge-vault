# Architecture

## Overview

`ai-knowledge-vault` uses a local-first file layout so humans, Obsidian, and AI agents can all work on the same source of truth.

## Layers

### 1. Timeline entries

Files in `knowledge/*.md` are the atomic knowledge entries.

Each entry keeps:

- frontmatter metadata
- `核心观点`
- optional `我的思考`
- full `原始内容`

### 2. Concept layer

`knowledge/concepts/*.md` is the compiled navigation layer.

Concept pages summarize:

- concept definition
- key insights
- representative entries
- related concepts

### 3. Reports layer

`knowledge/reports/*.md` stores reusable outputs produced by querying the vault, such as:

- topic lookup reports
- health reports

## Retrieval Model

The intended retrieval order is:

1. `_index.md`
2. matching concept pages
3. full entry content only when necessary

This keeps search fast while preserving access to the original source material.

## Why Obsidian

Obsidian provides:

- native Markdown storage
- wikilinks
- Dataview and Bases compatibility
- portable local files with no lock-in

## Extension Points

- add new concept heuristics in `knowledge_ops.py`
- add new ingestion workflows in `.claude/skills/kb/scripts/`
- add more report types under `knowledge/reports/`
