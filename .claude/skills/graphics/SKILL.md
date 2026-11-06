---
name: graphics
description: Motion graphics and overlays for Lumin ads with HyperFrames (HTML to video) — arrows, circles, check/cross marks, call-out labels, ingredient cards, price/offer cards, end cards, kinetic text. Use for "graphic", "overlay", "animate", "arrow", "end card", "offer card", "ingredient animation", or any designed element on top of footage.
---

# Graphics

HyperFrames renders HTML/CSS/GSAP animations to video. Its own skills (`/hyperframes`,
`/hyperframes-cli`, `/hyperframes-registry`) hold the format and the CLI; load `/hyperframes` first
and follow its render contract. This skill adds Lumin's rules.

## Rules
1. **Look**: `presets/graphics-style.md` (colours, fonts, motion). Follow any detail the editor gives
   literally (timing, colour, position); fill gaps from the style file and say which defaults you used.
2. **Overlays are separate layers.** Render with a transparent background (MOV with alpha, or WebM
   with alpha for CapCut) and place them on V2+ over the footage. Never bake a graphic into a
   generated clip or the main video.
3. **Start from the registry.** Search `/hyperframes-registry` for a block (arrow, highlight circle,
   checklist, lower third, end card) before building one by hand.
4. **Size**: 1080x1920 for 9:16, 1080x1350 for 4:5. Keep inside the safe zone (`presets/captions.md`).
5. **No claims in graphics** beyond what the script says. Offer details (price, guarantee days, bundle)
   come from the brief only; Lumin's site has had both 30 and 90 days in different places, so ask.

## Steps
1. One folder per graphic: `<job>/graphics/<name>/`. Scaffold with `npx hyperframes init` there (or
   copy `graphics/templates/<look>` if one exists).
2. Build, then `npx hyperframes check`, then look at frames from a preview before rendering.
3. Render (`npx hyperframes render`, transparent when it's an overlay), probe the output with
   ffprobe, pull 4 frames and look at them.
4. Put it on the timeline: add it to `timeline.json` on a V2+ track at the word it belongs to, or import
   it with the `premiere` skill.
5. When Salam approves a graphic, copy its folder to `graphics/templates/<look-name>/` and add one line
   to `presets/graphics-style.md` so it can be reused.

## Lumin graphics that come up often
- Red arrow / circle on thinning edges (problem shot), soft "wrong" SFX
- Red ✗ over the cause (relaxer box, tight braids, cheap biotin), green ✓ over Root Revive
- Ingredient cards: sea moss, black seed, turmeric, one line each
- "30-day supply · 2 capsules a day" product card
- Offer / guarantee card and end card with the bottle (real product photo)
