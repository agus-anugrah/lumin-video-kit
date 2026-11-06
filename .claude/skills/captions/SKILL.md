---
name: captions
description: Captions for Lumin ads — short meaning-based cards, word highlight, safe zone, as SRT for Premiere/CapCut or burned in. Use for "captions", "subtitles", "add text", "caption style", or the caption step of any job.
---

# Captions

Style rules are in `presets/captions.md`. Read them first.

1. Words come from the transcript of the **final audio** (the VO, or the cut UGC). For cut footage use
   the cut list so times match the timeline:
   `python3 scripts/captions.py <job>/transcript/words.json --out <job>/captions/captions --cutlist <job>/cuts/cutlist.json`
   For a VO-only ad leave out `--cutlist`.
2. Read `captions.srt` top to bottom and fix by hand:
   - every card reads as a little unit of meaning (1–4 words); never split a name, a number and its
     unit, or "Root Revive"
   - spelling of product and ingredient names: Lumin, Root Revive, sea moss, black seed, turmeric, CCCA
   - the transcript may mishear words (check against the script, which wins)
3. Deliver:
   - **Premiere**: import `captions.srt` and create a caption track (MCP `create_caption_track`), then
     tell the editor to apply the Lumin caption track style (Premiere can't set the style from a file).
   - **CapCut**: give the editor `captions.srt` to import (Text > Captions > import), or burn in.
   - **Burn-in / review**: set `"captions": "<job>/captions/captions.ass"` in `timeline.json` and render
     with `--burn-captions`. The `.ass` has the spoken word highlighted.
4. Check frames from the render: captions inside the safe zone, not covering a face or the bottle,
   readable on bright backgrounds.

Problem words: when the brief asks, a card with a "bad" word (relaxer, breakage, bald, thinning) can
get the red style, and the product/benefit card the green style (see `presets/captions.md`).
