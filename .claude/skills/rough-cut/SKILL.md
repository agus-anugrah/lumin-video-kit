---
name: rough-cut
description: Rough cut real footage (UGC creator videos, talking heads, testimonials, interviews) for Lumin ads — transcribe, remove pauses, fillers and retakes, pick the best takes, and hand over a timeline. Use for "cut this", "rough cut", "clean up this UGC", "remove the ums", "find the best takes", or any raw footage path an editor pastes.
---

# Rough cut

1. **Job**: `python3 scripts/new_job.py "<name>"`. Never move, rename or overwrite the editor's source
   files; refer to them by full path. Write the source paths into `job.md`.
2. **Look first**: `ffprobe` each file (length, resolution, fps, audio), and
   `bash scripts/frames.sh <file> <job>/review/src 6` to see what it is (selfie, mirror, ratio, light).
3. **Transcribe**: `python3 scripts/transcribe.py <file> --out <job>/transcript`.
4. **Find cuts**: `python3 scripts/cutlist.py <job>/transcript/words.json --out <job>/cuts`.
   Then read `cuts/cutlist.md` against `transcript/transcript.txt` yourself:
   - the retake finder is simple: when a creator says the same line twice, keep the better delivery,
     not always the last one; fix `cutlist.json` by hand
   - never cut inside a word; a cut lands in a real pause
   - keep breaths that carry emotion in personal-story ads; cut harder in offer ads
   - hooks: if the brief wants several hook options, mark each candidate (line + times) in `job.md`
5. **Compliance pass** on what the creator says: flag claims we can't make ("cured my alopecia",
   "doctor said", "grew back in 3 days", medical promises). List them in `job.md` with times; don't
   cut them silently, the strategist decides.
6. **Hand over**:
   - Premiere: `python3 scripts/xml_export.py <job>/cuts/timeline.json --out "<job>/timeline/<CODE>.xml"`
     and import with the `premiere` skill (new sequence, never the editor's open one).
   - CapCut / review: `python3 scripts/render.py <job>/cuts/timeline.json --out <job>/renders/<CODE>_rough.mp4`.
7. Report: kept length vs source length, number of cuts, flagged claims, anything you weren't sure about.

Multiple files (several creator takes): transcribe each, then build one `timeline.json` by hand that
takes the best line from each file in script order.

16:9 YouTube source that must become 9:16 with a blurred background: that's the Blur fill tool in the
Lumin app, not this kit.
