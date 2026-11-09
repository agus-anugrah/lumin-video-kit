---
name: broll
description: Make AI B-roll or short clips for a Lumin ad. Use whenever an editor asks for B-roll, a clip, a scene, a shot, "something for this line", a generated video or image, or pastes a script and asks what to show. Also for any follow-up on an existing job in jobs/.
---

# B-roll

Script line in, approved clip out. Five steps, two stops for the editor.

## 1. Understand the ask

Get, or pick a sensible default and say it in one line:
- **Script line(s)** the shot covers, and roughly how many seconds of VO.
- **Ratio**: 9:16 for VS, 4:5 for VM and VL (Lumin codes), else 9:16.
- **Preset**: `presets/ugc-iphone.md` unless the editor names another one in `presets/`.
- **Who is on screen**: default to the preset's default woman. If the ad already has a character,
  ask for a frame of her (or the clip) and use it as the reference.

Read `playbook/what-sells.md` ("Why the six bad ads failed") once per session. B-roll must show **her**
story beat, not just the word: on "I tried everything" show her bathroom shelf of oils, not a random
jar. If the ad has a protagonist, every shot of a woman is her (her Soul ID / reference frame), the
same age and look as the brief.

Turn each line into shots of 2–3 s (first 60 s of an ad) or up to 4 s (after that).
Each shot = one simple action a phone camera could catch. Not a story in one clip.

## 2. Plan, then stop

Create the job (or reuse the ad's existing job): `python3 scripts/new_job.py "<name>" --editor <name>`.
Fill the header and the Shots table in its `job.md`.

Before generating anything, look for a clip we already have: earlier jobs' `clips/` folders and the
Lumin app's B-roll library. Reuse first, generate only what's missing.

Show the table, the image model and video model you will use, how many outputs (default 3 stills
per shot, 1 video per picked still), and the credit balance. **Wait for "go".**

Pick models by checking what the CLI offers today (`higgsfield model list`, `higgsfield model get <id>
--json`). Defaults: a realistic photo model (Nano Banana Pro, Seedream or Soul) for UGC stills, Kling 4.0
for B-roll clips, Seedance 2.5 for anything with lip sync. If the editor has no Higgsfield sign-in,
use the Figma connector's Weave models (`weave_find_model` / `weave_run_model`) and confirm each quoted
cost. Write down the model ids you used in `job.md` so the next job can reuse what worked.

Same woman in more than 3 shots: train a Soul ID once from her approved still/sheet
(`higgsfield soul-id`) and generate her stills with it.

## 3. Stills

For each shot, write one complete prompt from the preset blocks (look, camera, light, person) plus
the shot's action. Attach references: character frame if any, product photos from
`references/product/` if the bottle is in shot, and 1–2 style frames from
`references/style/loved/` that match the scene.

Generate, save into `jobs/<...>/stills/<shot#>_<n>.jpg`, then run the **quality check** below on
each one. Regenerate a failed still at most twice with a fixed prompt; if it still fails, keep the
best and flag it.

**Stop:** show the passing stills per shot and ask the editor to pick one per shot (or "redo 3").

## 4. Clips

For each picked still, write a short motion prompt: one movement, handheld, natural speed, no
camera tricks, no talking unless asked. Duration = the shot's seconds, within the model's limit.
Generate, save to `jobs/<...>/clips/<shot#>.mp4`, pull frames
(`bash scripts/frames.sh <clip> <job>/review/<shot#> --fps 4`) and run the quality check on the frames, plus: no morphing, no extra fingers appearing mid-clip, hair doesn't change texture,
bottle label stays readable.

## 5. Hand over

Update `job.md` (status per shot, model ids, prompts used, credits spent, any flags). Tell the
editor where the clips are. If Salam later approves or rejects a clip, note it in `job.md`, and if
the reason is a new rule, add one line to `rules.md`.

## Quality check (look at the image, don't assume)

Reject if any of these:
- **Hair**: texture looks plastic, smeared, wet-look by mistake, or not like real 4A–4C / relaxed /
  braided hair as the shot needs; edges or hairline melted or painted on; wig line wrong.
- **Skin**: airbrushed, waxy, too smooth, wrong age, lighter than the reference.
- **Hands / body**: wrong finger count, merged fingers, broken wrists, objects fused into hands.
- **Product**: bottle shape, colour or label not matching `references/product/`; any made-up text.
- **Look**: anything on `presets/never.md` (cinematic grade, studio light, perfect framing, stock
  photo smile, etc.).
- **Fake proof**: anything that shows hair improving or a result (rule 3 in CLAUDE.md).
- **Wrong person**: not the ad's protagonist when it should be her; wrong age for the brief; glam model look.

Write the reason for every rejection in `job.md`; it's how the presets get better.
