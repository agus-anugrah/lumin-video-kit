---
name: research
description: Research a Lumin batch before planning it - competitors' top ads (from TrendTrack, saved daily in the Lumin app) and Lumin's own top ads around the batch's date - and turn them into findings and a proposed brief. Runs automatically as step 0 of every "make batch <code>" (ai-ad). Also use when someone asks "what are competitors running?", "research batch 129", "what's working for Azure/Resilia right now?", or wants fresh hook ideas.
---

# Research

Salam's rule: before we make an ad, we look at what's working **right now**: competitors' top ads around the
batch's date, and our own. Every one of our story formats came from a competitor's winner (`playbook/formats/README.md`).

## 1. Get the data (no credits: the app already saved it)

`python3 scripts/lumin_batch.py get <code>` runs this for you. On its own:
`python3 scripts/lumin_batch.py research <code> [--date YYYY-MM-DD] [--refresh]`

It writes `<job>/research/`:
- `research.md`: our top creatives in the 30 days before the date, then the strongest competitor ads in the 14 days
  before it (at most 2 a brand): days running, copies, where it ranked, offer, landing page, hook, full transcript,
  copy, and the video and frames on disk.
- `videos/`, `frames/<ad>/` (6 frames each), `competitor_ads.json`.

The brands are the competitors marked "Pull their top ads daily" in the app (Competitors page). The date is the batch's
launch date (or today). If research ran in the last 3 days it's reused; `--refresh` redoes it.

If it says no competitor ads are saved yet, the daily pull hasn't run: say so in one line and go on with the plan.

## 2. Read it properly

For every competitor ad: read the transcript and copy, and **look at the frames** (open the images). Note:
- **Hook**: the first sentence, and the first frame. Who, what happened, which number.
- **Format**: UGC talking head, 3D Pixar, song, movie drama, podcast, demo, listicle, founder, product-talks.
- **Beats**: the order of the story (map it to our beat maps where it fits).
- **Look**: real or AI, setting, camera, captions style, how the product is shown.
- **Offer and CTA**: discount, bundle, guarantee, urgency, landing page type (product page, listicle, advertorial).
- **Strength**: WINNER (high in 2+ lists, or 30+ days with 3+ copies) beats a fresh test.
Music-only ads have no transcript: judge them from the frames, or transcribe the video if it's sung.

## 3. Write Findings and Proposed brief (in research.md, replacing the placeholders)

**Findings** (short, plain sentences):
- What's working for them right now: 3–6 patterns that show up in more than one winner (hooks, formats, offers, looks).
- What's new: anything we haven't run (compare with our top ads in the same file and `playbook/what-sells.md`).
- What not to copy: claims we can't make, men's products, off-avatar, anything that would break `presets/never.md`.

**Proposed brief**, for this batch's format (its beat map in `playbook/formats/`):
- 3 hooks adapted to Lumin and the batch's angle, each one line, at least one the blunt confrontation, each noting
  which competitor ad it came from.
- The beats, adjusted with what the research showed.
- The look (preset and 1–2 reference ads with their frames).
- The offer and CTA (only facts from the batch's brief; competitors' offers go in as ideas for the strategist).

## Rules
- **The strategist's brief and script win.** If the batch already has a script, the research gives suggestions (hooks,
  visuals, fixes for `sell-check`), not a rewrite. With no script, the proposed brief is what the script is drafted from.
- Never copy a competitor's ad: no lifting their words, characters, footage or claims. Learn the pattern, write our own.
- Their claims are theirs: never carry over a medical claim, a number or a testimonial.
- Days running and copies are signs of money, not proof. Say "likely winner", never "their best seller".
- Show the editor a 5-line summary when it's done: the top 3 patterns, the 3 hooks, and which reference ad to watch.
