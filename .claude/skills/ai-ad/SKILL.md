---
name: ai-ad
description: Turn a Lumin ad script (and brief) into a full AI-generated ad draft — voiceover, character and product sheets, storyboard, clips, captions, music and an assembled first cut. Use when an editor pastes a script or brief and asks to "make the ad", "storyboard this", "generate the video", "make characters", "do the VO", or continues a job started this way. For single shots inside an existing edit, use the broll skill instead.
---

# AI ad

Script in, first cut out. Four stops where a person decides; everything between them runs on its own.

The goal is an ad that **sells**, not just a fast one. Read `playbook/what-sells.md` before planning:
it holds the winning structure, the hook patterns, the numbers, and why the team's earlier AI remakes
failed (different women in every shot, fake before/afters, wrong age, glossy look). Then read the
**beat map for the batch's format** (`brief.md` names it under "Format family"; all of them are in
`playbook/formats/`): 3D Pixar, Song, Movie drama, Story VSL or Sale. Run the `sell-check` skill at the
plan and at the end.

```
brief + script ─► 1 plan ─► STOP ─► 2 voiceover ─► STOP ─► 3 sheets ─► STOP ─► 4 storyboard
   ─► STOP ─► 5 clips ─► 6 sound + captions ─► 7 assemble ─► 8 review
```

Start from the batch in the Lumin app when there is one: `python3 scripts/lumin_batch.py get <code>`
(or part of its name). It creates the job folder with `brief.md` (angle, awareness, funnel, audience,
format, hooks, files) and `script.txt` (the batch's own script tab). Read both before planning. The
brief and script from the strategist win over the playbook; the playbook fills gaps and powers the
sell check. No batch: `python3 scripts/new_job.py "<ad code or name>" --editor <name>` and ask for the
script. Everything for this ad lives in that job folder; keep `job.md` current after every step.

## 1. Plan

Read the brief and script. Write into `job.md`:
- **Angle** (offer, industry expose, transformation, personal story, objection, ancient African story…)
  and **format**: VS 9:16 short, VM 4:5 medium, VL 4:5 long (Lumin codes). Default 9:16.
- **Format family** and its beat map (from `brief.md`; unknown = ask the strategist).
- **Preset** from `presets/`, one for the whole ad. By format: 3D Pixar and Song → `3d-animated`;
  Movie drama → `realistic-drama` ("Movie scene" section); Story VSL and Sale → `ugc-iphone`,
  `realistic-drama` or `ancient-story`, whichever fits the angle.
- **Cast**: each recurring person (age, look, hair situation, wardrobe, home). Default from the preset.
- **Scene table**: one row per script line → what we see, shot type (talking head TH / B-roll / product /
  graphic / real UGC needed), place. Mark any line that needs **real proof** (before/after, results,
  testimonials) as "REAL UGC NEEDED"; never generate it.
- **Never-show list** for this ad (from `presets/never.md` plus anything in the brief).
- **Protagonist**: the one woman whose story it is (age, look, hair situation, home). Every "I" shot is her.
- **Real or AI per line**: in a Story VSL or Sale ad, trust beats (hook problem shot, hiding, scalp
  close-ups, "me now", proof) are REAL NEEDED first: search the Lumin B-roll library and creator footage
  before planning AI. AI covers animation, mechanism, product (from real photos), places, props and
  filler. 3D Pixar, Song and Movie drama are fully AI by design: they're clearly a cartoon or a movie
  scene, never presented as a real customer (see each beat map's production notes).
- **Beat map**: tag each script line with its beat from the format's beat map. The visual for a line
  comes from its beat and her story, not from the single word being said. Missing beats go in the
  sell check.
- **Hooks**: the beat maps show Meta always spent on the bluntest hook (who shamed her, what they said
  about her hair, who watched). If all of the script's hooks are soft, propose one blunt rewrite.
- **Credit estimate** for the whole run (`higgsfield generate cost ...` per model, or Weave quotes).

Run `sell-check` on the script. If there's no script yet, draft one on the format's beat map with 3 hook
options (one of them the blunt confrontation) for the strategist to approve; never generate from an
unapproved script.

**Stop:** show the plan, the sell-check table and the estimate. Wait for "go" or changes.

## 2. Voiceover

Load the `voice-music` skill. Pick 3 voice candidates that match the speaker (age, accent, warmth) and
render the first line with each (1 generation each). **Stop:** editor picks. Then render the full VO
(max 2 takes), transcribe it for word timings (`scripts/transcribe.py` on the VO file), and fill the
seconds column of the scene table from the real timings.

If the script has a talking head, the VO file is also the lip-sync audio for Seedance.

By format:
- **3D Pixar / Movie drama**: dialogue, so one voice per character (pick 3 candidates for each main
  character the same way) plus the narrator if there is one. Render line by line into `vo/<scene>_<line>`
  so each Seedance dialogue shot gets its own audio.
- **Song**: the song is the voice. Follow "Songs" in the `voice-music` skill: the editor makes it on
  suno.com from the lyrics you prepare, you transcribe it for timings. No separate VO.

## 3. Sheets (who and what stays the same)

For each cast member: one **character sheet** (front, three-quarter, profile, full body, hair close-up
showing her actual hair situation) in the preset's look, on a plain background, no text. **The protagonist always gets a Soul ID**
(`higgsfield soul-id ...`) trained from her approved sheet, and every still of her uses it. Supporting
people who appear more than twice get one too. Keep her age, skin tone, face and hair situation
identical across the whole ad; only the story moment changes.

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

Check every frame for the protagonist's face against her sheet (a different face is a fail, even if the
image is pretty), age and look against the brief, and the playbook's "why the bad ads failed" list.
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

Run `sell-check` on the finished ad, then the `finish` skill: loudness, frame check, safe zones,
never-list, the strategists' 12 editor rules, then the hand-over message with what's done, what's
flagged, and credits spent.

## Warm-traffic (sale) ads
Short version of the same flow: hook = the offer, 15–70 s, the real bottle on screen early and at the CTA,
urgency (ends at midnight, sells out), a 2-line story from the protagonist, guarantee, "tap below".
