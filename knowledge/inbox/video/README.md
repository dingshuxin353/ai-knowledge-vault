# Video Inbox

This folder is for video and audio ingestion.

It supports a workflow where raw media is transcribed, lightly cleaned, and then written into the main knowledge vault as a formal entry.

## Subfolders

- `raw/`: input media files such as `.mp4`, `.m4a`, `.mp3`, `.wav`
- `work/`: temporary files created during processing
- `transcripts/`: raw transcripts, cleaned transcripts, and metadata
- `logs/`: ingestion logs

## Suggested workflow

1. Put media files into `raw/`
2. Configure `.claude/skills/kb/config.local.json`
3. Run `python3 .claude/skills/kb/scripts/video_ingest.py`
4. Review the generated entry in `knowledge/`
5. Fill in `核心观点` if it is still empty

## Notes

- `work/` is temporary and usually should not be committed
- transcript artifacts are useful for debugging and audit trails
- this flow is optional; the vault can be used without any transcription feature
