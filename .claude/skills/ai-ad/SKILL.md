---
name: ai-ad
description: Turn a Lumin ad script (and brief) into a full AI-generated ad draft — voiceover, character and product sheets, storyboard, clips, captions, music and an assembled first cut. Use when an editor pastes a script or brief and asks to "make the ad", "storyboard this", "generate the video", "make characters", "do the VO", or continues a job started this way. For single shots inside an existing edit, use the broll skill instead.
---

# AI ad

Script in, first cut out. Four stops where a person decides; everything between them runs on its own.

```
brief + script ─► 1 plan ─► STOP ─► 2 voiceover ─► STOP ─► 3 sheets ─► STOP ─► 4 storyboard
   ─► STOP ─► 5 clips ─► 6 sound + captions ─► 7 assemble ─► 8 review
```

Start: `python3 scripts/new_job.py "<ad code or name>" --editor <name> --batch "<batch>"`. Everything for
this ad lives in that job folder; keep `job.md` current after every step.

## 1. Plan

Read the brief and script. Write into `job.md`:
- **Angle** (offer, industry expose, transformation, personal story, objection, ancient African story…)
  and **format**: VS 9:16 short, VM 4:5 medium, VL 4:5 long (Lumin codes). Default 9:16.
- **Preset** from `presets/` that fits the angle (`ugc-iphone`, `realistic-drama`, `ancient-story`,
  `3d-animated`). One preset for the whole ad.
- **Cast**: each recurring person (age, look, hair situation, wardrobe, home). Default from the preset.
- **Scene table**: one row per script line → what we see, shot type (talking head TH / B-roll / product /
  graphic / real UGC needed), place. Mark any line that needs **real proof** (before/after, results,
  testimonials) as "REAL UGC NEEDED"; never generate it.
- **Never-show list** for this ad (from `presets/never.md` plus anything in the brief).
- **Credit estimate** for the whole run (`higgsfield generate cost ...` per model, or Weave quotes).

**Stop:** show the plan and the estimate. Wait for "go" or changes.

## 2. Voiceover

Load the `voice-music` skill. Pick 3 voice candidates that match the speaker (age, accent, warmth) and
render the first line with each (1 generation each). **Stop:** editor picks. Then render the full VO
(max 2 takes), transcribe it for word timings (`scripts/transcribe.py` on the VO file), and fill the
seconds column of the scene table from the real timings.

If the script has a talking head, the VO file is also the lip-sync audio for Seedance.

## 3. Sheets (who and what stays the same)

For each cast member: one **character sheet** (front, three-quarter, profile, full body, hair close-up
showing her actual hair situation) in the preset's look, on a plain background, no text. If she appears
in more than 3 shots, train a Soul ID from the approved sheet (`higgsfield soul-id ...`) and use it for
every still of her.

Product: the bottle comes from `references/product/` (real photos), never generated from words. Use
`higgsfield product-photoshoot` when a clean product still in a new setting is needed.

Sets: one establishing still per recurring place (her bathroom, her bedroom, the salon, the church),
so every shot in that place matches.

Check every sheet with the quality check in the broll skill. **Stop:** show the sheets, wait for
approval or fix notes. A fix = regenerate only that sheet with the full corrected prompt.

## 4. Storyboard

For each scene: write the first-frame still prompt (preset blocks + scene + attached sheets + 1–2
loved style frames), generate 2 options, check them, keep the best. Save as
`stills/<scene#>_<n>.jpg`. Lay them out in order with line, seconds and shot type:
publish a storyboard page as an Artifact (grid of stills with captions) so Salam can comment on it,
and also write `review/storyboard.md`.

Fix failing frames yourself (max 2 retries each), flag what still fails.

**Stop:** "Storyboard ready." Show the summary table (scene, secs, shot, QA result, retries) and ask
for the video model, resolution and the go. Default: Kling 4.0 for B-roll, Seedance 2.5 for talking
heads (VO as audio reference), 720p, the ad's ratio.

## 5. Clips

Per scene: image-to-video from the approved still, motion prompt = one natural action, handheld,
duration = the scene's seconds rounded up within the model's limits (generate a little longer than
needed, trim in the edit). Talking heads: Seedance 2.5 with the VO segment as audio. Save to
`clips/<scene#>.mp4`, pull frames (`bash scripts/frames.sh <clip> <dir> --fps 4`) and check them:
no morphing, hair texture and skin stay the same, hands correct, bottle label stays the real one,
no fake proof. Retry failures once with a fixed prompt; flag the rest.

## 6. Sound and captions

- Captions: `captions` skill, from the VO words.
- Music: `voice-music` skill (instrumental only; vocal check must pass). Music goes in last.
- SFX: a few, subtle (whoosh on hard cuts, soft ding on the product reveal). Keep the clip's own
  ambient sound when it's good.

## 7. Assemble

Write `timeline/timeline.json` (format in `scripts/timeline.py`): A1 = VO, A2 = music at the
preset's bed level, A3 = SFX; V1 = scenes in order on the VO timing; V2+ = overlays/graphics.
Cut on the VO: a scene starts on its first word, never before. Then:
- Premiere editors: `python3 scripts/xml_export.py timeline/timeline.json --out "<job>/timeline/<CODE>.xml"`,
  then the `premiere` skill to import it (or the editor imports it by hand).
- Everyone: `python3 scripts/render.py timeline/timeline.json --out renders/<CODE>_v1.mp4 --burn-captions`
  as the review video (CapCut editors get this plus the clips and captions.srt).

## 8. Review

Load the `finish` skill: loudness, frame check, safe zones, never-list, then the hand-over message
with what's done, what's flagged, and credits spent.
