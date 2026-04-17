# Concepts Folder

This folder stores compiled concept pages.

Concept pages are the navigation layer between the high-level index and the raw entry files in `knowledge/*.md`.

## What goes here

- concept definition
- key insights aggregated from entries
- representative entry links
- related concept links
- optional Dataview query blocks

## Typical lifecycle

1. You collect timeline-style knowledge entries in `knowledge/*.md`
2. Run `python3 .claude/skills/kb/scripts/knowledge_ops.py compile`
3. The script generates or refreshes concept pages here

## Naming

Use one file per concept, for example:

- `第二大脑.md`
- `上下文工程.md`
- `Claude协作工作流.md`

## Example

See [`EXAMPLE.md`](./EXAMPLE.md) for a minimal concept page shape.
