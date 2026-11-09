# Captions style

> From Lumin's profitable ads (Batch 79, Batch 84 remake, Sale #65), 2026-11-09.

- **Look (default)**: bold black text on a **white rounded box**, sentence case, 2 short lines at most.
  That is what every profitable ad uses, hook included. No per-word colour.
- **Hook text**: same box style, on screen from the first frame, the hook in her words
  ("I'm a 47 year old black woman who went from hiding my scalp").
- **Sale ads**: an offer banner on screen the whole time (e.g. black "SAVE 60% OFF" on yellow at the top)
  and the hook as a comment-reply sticker ("Reply to Samantha's comment: …").
- **Cards**: 1–8 words split by meaning; never split "Root Revive", a number and its unit, or a name.
- **Story formats (3D Pixar, Song, Movie drama) use "outline" instead** (`captions.py --style outline`):
  white text with a dark outline or shadow, 2–4 words a card, lower middle. That's what all four story
  winners use (watched 2026-11-09). abusiveman and pregnant-aunt colour one key word yellow ("NOT
  **GENETICS** NOT", "**starves** the roots"); Lymphoria and School Reunion keep it all white. The box
  would cover the faces these ads live on.
- **Optional burn-in style "outline"** in the other formats only when the brief asks for it.
- **Problem / solution colour** (only when the brief asks): a red word box on a problem word, green on
  the Root Revive card.
- **Safe zone (9:16, 1080x1920)**: text between y 300 and y 1620, away from the right edge (x > 940)
  where Meta/TikTok buttons sit. Default position: lower middle, about 520 px from the bottom, moved up
  when it would cover a face, hands, the scalp being shown or the bottle.
- **4:5 (1080x1350)**: same rules, about 260 px from the bottom.
- Spell names exactly: Lumin, Root Revive, black seed, bamboo, pumpkin seed, sea moss, turmeric, CCCA.
