---
name: premiere
description: Work inside Adobe Premiere Pro through the Premiere MCP — import an XML edit, media, captions or graphics, place clips, read the timeline, export. Use whenever a step says "in Premiere", the editor asks to put something on their timeline, or a Premiere project/sequence is mentioned.
---

# Premiere

Uses the `premiere-pro` MCP server (open-source Adobe_Premiere_Pro_MCP, CEP bridge). The editor must
have Premiere open with a project, and the **MCP Bridge (CEP)** panel started
(Window > Extensions > MCP Bridge (CEP) > Start Bridge).

The server shows a few tools by default; use `search_tools` → `get_tool_schema` → `invoke_tool` for
the rest (or the server is started with the full tool list, see `.mcp.json`).

## Rules
1. **Every session starts with `verify_premiere_connection`.** If it fails, tell the editor the exact
   step (open Premiere, open the project, start the bridge) and stop.
2. **Read before you write.** List sequences and tracks first. Never change the editor's active
   sequence unless they ask; build in a **new sequence** named with the ad code (e.g. `VS-312-A`).
3. **First drafts go in as XML**, not clip by clip: `scripts/xml_export.py` then `import_fcp_xml`.
   Clip-by-clip MCP edits are for small revisions inside an existing sequence.
4. **Read back after every change** (track list / timeline summary). Don't say it's done until the
   read-back shows it.
5. **Ask first** before deleting clips or media, overwriting an export, saving over the project, or
   closing it.
6. **Video-only placement for B-roll**: when placing a generated clip over a talking head, place it on
   V2+ video only, so it doesn't replace A1. Linked-audio inserts can overwrite the VO; check A1 after.
7. **Replacing a clip** can shift or overwrite its neighbours: note the neighbours' in/out before,
   compare after.
8. Import originals (the generated MP4s, the real UGC files), not re-renders, so editors keep full quality.

## Common jobs
- Import a draft: `import_fcp_xml` with `<job>/timeline/<CODE>.xml` → read back the new sequence.
- Captions: `import_media` the SRT → `create_caption_track` → remind the editor to apply the Lumin
  caption style.
- Graphics: `import_media` the rendered overlay → place on V2+ at the right time → read back.
- Markers from Salam's feedback: list markers, turn each into a to-do in `job.md`, fix, read back.
- Export: only when asked, with the path confirmed; specs in `presets/export.json`.
