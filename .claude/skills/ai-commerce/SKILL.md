---
name: ai-commerce
description: Use the AI Commerce Ad Engine connector (format library, storylines, flip engine) and Kie generation (Seedance 2.5, Wan 3.0, nano-banana-pro pictures, Suno V6 songs) inside the kit's own ad process. Use whenever someone asks to make a Lumin ad "with AI Commerce", names an AI Commerce format or storyline (V22, V101, T221…), pastes a competitor ad to "flip", or asks to render with Kie or Seedance on Kie. The kit's pipeline, stops and rules always apply; AI Commerce never runs its own one-shot flow for Lumin.
---

# AI Commerce inside the kit

AI Commerce is a library and a second generator for the kit, never a separate process. Lumin ads made with it go
through the same steps as every other ad: **research → plan → STOP → voice → STOP → sheets → STOP → storyboard →
STOP → clips → sound and captions → assemble → review** (the `ai-ad` skill). This file only says what changes at
each step when AI Commerce is used.

## Never
- Never run the engine's one-command flip (`flip_plan.py run`, the "one-shot flip", "ask no questions") for Lumin.
  Its instructions say to produce everything in one go; the kit's stops win.
- Never generate anything (picture, clip, song) before the step's stop is approved, and never before the editor has
  seen the Kie quote and said go (kit rule 7).
- Never let the library override the kit. Lumin's beat maps (`playbook/formats/`), `playbook/what-sells.md`, the
  research and the strategist's brief come first. A library card is an idea source.
- Never carry a competitor's words, claims, characters or footage into a flip. Learn the pattern, write our own.

## Step by step

**0. Research (`research` skill, unchanged).** Run it first, always. The proven competitor ads it finds (30+ days
running or many copies) are the best references to flip. Note their video link or file in `research/research.md`.

**1. Plan (`ai-ad` step 1 + this):**
- Read the AI Commerce brand profile (`get_brand_profile` "Lumin"). Its section 13 is a copy of this kit's playbook;
  if it disagrees with the kit, the kit wins and the profile needs a re-copy (tell the editor).
- If the ad flips a reference (a competitor winner from the research, or a link the strategist gave): describe it
  to `analyze_example_ad` or open the matching card with `get_format`, and use the result to fill the scene table:
  its beats, pacing and devices, mapped onto Lumin's beat map for the format. Say which card or storyline you used.
- Matching cards (`playbook/formats/README.md`): 3D Pixar → V22 + workflow `3d-animated-stories`; Song → V101 +
  `song-ads`; Movie drama → V39 / V23; Story VSL → V87, UGC → V44, Podcast → V03; Sale → V62; mechanism → V04.
- Run `sell-check` (line 3b matters most here: a new format on an old script needs a new trigger).
- **Generator choice** in the plan: Higgsfield (default) or Kie. Quote Kie with
  `python3 scripts/kie.py quote --model seedance|wan --res 480p|720p --seconds <total> --pictures <n> --songs <n>`
  and show it next to the Higgsfield estimate. Kie prices (Nov 2026): Seedance 2.5 $0.14/s at 480p, $0.315/s at
  720p; Wan 3.0 $0.04/s at 480p; a picture about $0.09; a song call about $0.06. 200 credits = $1.
- **Stop.** Plan, sell-check table, both estimates. Wait for "go" or changes.

**2. Voice.** As in `ai-ad`. For a Song, Kie can make the song from the lyrics instead of the editor on suno.com:
write the lyrics with `[Verse]` tags only (no repeated chorus), then
`python3 scripts/kie.py song <job> --lyrics <file> --style "<from the song beat map>" --title "<name>" --seconds <lyrics length + 15>`.
Set `--seconds` about 15 s longer than the lyrics need or Suno cuts the last lines. It returns two versions; the
editor picks. Transcribe the pick for word timings (`scripts/transcribe.py`).

**3. Sheets.** With Kie: `python3 scripts/kie.py picture <job> --id <name> --prompt "<sheet prompt>" [--ref <earlier sheet>]`.
Write the age as a number and say "NOT young" when she's 40+: cartoon models drift to 25. The product is never
drawn: use `references/product/`. **Stop** for the sheets, as usual.

**4. Storyboard.** First-frame stills per scene from the approved sheets (`kie.py picture … --ref <sheets>`), checked
like any still, laid out as the storyboard page. **Stop: "Storyboard ready."** Ask for the model, resolution and go.

**5. Clips.** With Kie: one call per scene or per group of scenes up to 15 s:
`python3 scripts/kie.py clip <job> --id <scene> --seconds <s> --prompt "<shots with timings>" --ref <approved still and sheets> [--model seedance] [--res 480p] [--audio]`.
Seedance names references `@image1…`; the script adds the legend. Use `--audio` only when the clip's own voices are
the dialogue; leave it off when the VO or song carries the sound. Models cut where they like: run scene detection on
each clip before captioning, and time captions to the real cuts. Check frames as in `ai-ad` step 5. Phone screens
and small label text come out garbled: cover them in the edit or redo the shot.

**6–8. Sound, captions, assemble, review.** Unchanged (`captions`, `voice-music`, `finish`).

## Money
`kie.py` writes every paid call to `<job>/kie/ledger.json` before sending it and refuses past the approved
ceiling. After the editor says go: `python3 scripts/kie.py approve <job> --reply "<their exact words>" --ceiling <usd>`.
Never write the approval for them. `kie.py spent <job>` and `kie.py balance` for the hand-over. A timeout or dropped
connection is not a failure: `kie.py fetch <job>` downloads what finished without paying again.

## Setup
`KIE_API_KEY` in the editor's shell profile (never pasted into chat). The AI Commerce connector is added in the
editor's own Claude. Without either, use Higgsfield as usual.
