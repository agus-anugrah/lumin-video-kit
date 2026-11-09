# References

## product/
- `bottle_in-hand_real-photo.jpg`: the **real bottle**, held in a hand. Source of truth for shape, cap,
  label layout and colours (black label, white "ROOT REVIVE", gold ingredient lines, a beige/tan band
  at the bottom, ridged silver cap, clear bottle with white capsules).
- `bottle_front_clean.jpg`: clean front shot on a plain background (the store image). Best reference for
  label text. Its bottom band is shinier gold than the real bottle's beige band, and it writes
  "ingredients" in lower case; when they differ, match the real photo.

Label text (exact): Lumin · ROOT REVIVE · BLACK SEED EXTRACT · BAMBOO EXTRACT · PUMPKIN SEED EXTRACT ·
+17 Growth Ingredients · DIETARY SUPPLEMENT · 60 CAPSULES.

Every product shot attaches both images. Never let a model write the label from a prompt; reject any
still or clip where the label text, colours or bottle shape differ from these.

Still nice to have: back of the bottle, side, top, two capsules in a palm, bottle on a bathroom counter.

## style/loved/ and style/hated/
Frames from Lumin's own ads (Meta previews, Nov 2026). The file name says the ad, its ROAS and what the
frame shows. These are small screenshots (about 147x182, with the player bar), so use them as
**direction for the look and the shot**, not as image references for generation.

- **loved/**: the profitable ads (Batch 79 VSL ROAS 1.28, Batch 84 remake 1.06, Sale #65 1.17). Real,
  raw footage: real scalps and edges, scalp camera, real women at home, a real bottle in a real place,
  black-on-white caption boxes, simple 3D for the mechanism.
- **hated/**: the AI-realistic ads that lost money (Church v2 ROAS 0.64) and the six flops (contact
  sheets): glossy AI women, a different face in every shot, before/after as two people, 20-somethings
  for a 50+ hook, men, scraped low-res clips, tiny captions.

Read `playbook/what-sells.md` for the full story behind them.
