---
name: finish
description: Final checks and delivery for a Lumin ad — loudness, frame review, safe zones, never-list and claims check, export specs, hand-over note. Use for "check it", "review", "QA", "export", "is it ready", or the last step of any job.
---

# Finish

Nothing is "done" until each line below has been checked and written in `<job>/review/REVIEW.md`.

## Checks
1. **Render or export exists** and plays: `ffprobe` shows the right size (1080x1920 for 9:16,
   1080x1350 for 4:5), fps, length, and an audio stream.
2. **Loudness**: `python3 scripts/loudness.py measure <file>` → about −14 LUFS, true peak ≤ −1 dBTP.
   Normalise a copy if not (`normalize`), never overwrite the editor's export.
3. **Frames**: `bash scripts/frames.sh <file> <job>/review/frames 16` and look at every frame:
   - generated people: hair, edges, skin and hands consistent from shot to shot
   - the bottle is the real one in every product shot
   - captions inside the safe zone, not over faces or the bottle
   - nothing from `presets/never.md`
4. **Claims**: no before/after or results that were generated; no medical promises; offer details
   match the brief. List anything doubtful for the strategist.
5. **Sync**: B-roll never starts before the word it shows; captions match the audio.
6. **Music**: vocals check passed; music ends cleanly (fade, no cut-off note).

## The strategists' 12 editor rules (from Lumin's script docs; all must pass)
1. The hook is visually impactful (no boring or dull hooks).
2. Captions have zero grammar, spelling or punctuation errors.
3. Visuals always follow and reinforce every caption / voice line.
4. The voiceover is consistent in tone, pacing and volume throughout.
5. All text and key visuals stay fully inside safe zones.
6. All visuals are high quality (no blurred copied videos).
7. All videos are unique (no copying).
8. The product stays clearly visible and is never repeatedly blocked by captions or overlays.
9. The audio mix is clean and balanced (no harsh peaks, music never overpowers the VO).
10. CTA, offer and end frame are correct, clear and match the brief exactly.
11. Every scene holds long enough for captions and visuals to be read without rush.
12. Key claims, benefits and moments from the brief are all included accurately.

If a rule can't be followed because of the concept style, write why in `job.md` (the strategists ask
for that note). Then run `sell-check` lines 13–15.

## Deliver
- Specs: `presets/export.json`. Name files with the ad code (`VS-312-A.mp4`), no "final", "v2-new".
- Ask before overwriting any file.
- Hand-over message to the editor: what's done, the file path(s), flagged issues with times (m:ss),
  credits spent on this job (from `job.md`), and what still needs a person (style, Salam's review).
