# Formats: which beat map to use

Every batch in the Lumin app has a **Format**. `lumin_batch.py get` turns it into a format family and
writes the matching beat map into `brief.md`. Plan the ad on that beat map; `sell-check` checks against it.
If the format is empty or unknown, the batch reader looks for a format line in the script's header
("Format/Style", "AD FORMAT"). Still nothing: ask the strategist.

| Family | App labels | Beat map | Closest AI Commerce cards |
|---|---|---|---|
| **3D Pixar** | Pixar-Style VSL, AI Pixar VSL, Animation Ad, AI - Talking - Animated | `pixar.md` | V22 + workflow `3d-animated-stories` (VSL arc V87) |
| **Song** | Pixar-Style Song, Singing Animation, AI - Singing - Animated, AI Song | `song.md` | V101 + workflow `song-ads` |
| **Movie drama (full AI)** | Movie Scene AI, Cinematic, Real-Life Cinema, AI Movie Style | `movie-drama.md` | V39 (scripted drama), V23 (photoreal mini-movie) |
| **Story VSL** | VSL, Personal VSL, B-roll VSL, AI-VSL, AI Talking Head VSL, Voiceover w/ b-roll, Podcast, UGC Talking head, Transformation | `../what-sells.md` (the 12-beat VSL) | V87 (VSL), V44 (UGC talking head), V03 (podcast) |
| **Sale** | Sale Ad | `../what-sells.md` (sale ad) | V62 (comment-reply video) |
| Mechanism insert | (inside any format) | the beat map's mechanism beat | V04 (3D "what happens inside") |
| Static | Static | not a video; the kit doesn't make statics | — |

The AI Commerce column maps our families to the AI Commerce Ad Engine connector's format cards, for
anyone planning a Lumin ad there. The Lumin brand profile in that connector (section 13) is a copy of this
playbook: the kit is the source, so change it here first.

New labels appear all the time. Map a new one by what the ad *is* (animated? sung? a movie scene?), and
add it to this table and to `FAMILIES` in `scripts/lumin_batch.py`.

## Last 30 days by family (to 2026-11-23, Meta-reported)

Winners = batches over $5,000 spent. Full rows by app label in `../what-sells.md` ("Last 30 days").

| Family | Labels counted | Tested | Winners | Spend | ROAS |
|---|---|---|---|---|---|
| 3D Pixar | Pixar-Style VSL 3/7 (0.75), Animation Ad 1/23 (0.73), AI Pixar VSL 0/7 (0.83) | 37 | 4 | $92.9k | 0.73–0.83 |
| Song | Pixar-Style Song | 13 | 1 | $28.3k | 0.83 |
| Movie drama | Movie Scene AI 1/4 (0.72), Cinematic 1/5 (0.58) | 9 | 2 | $12.9k | 0.58–0.72 |
| Story VSL | UGC Talking head 8/45 (0.86), VSL 10/46 (0.82), Voiceover w/ b-roll 0/14 (0.95), Personal VSL 0/8, B-roll VSL 0/7 | 120 | 18 | $132k | 0.31–0.95 |
| Sale | Sale Ad | 9 | 1 | $17.0k | 0.93 |
| Account | all ads | — | — | $403.6k | 0.82 |

Since 2026-11-09: Pixar-Style VSL wins most often (3 of 7) but Animation Ad (1 of 23) and songs (1 of 13)
rarely do, and the latest calls show why: songs and AI Pixar VSLs made from old winning scripts lost (see
`../what-sells.md`, "Latest calls"). Each story ad needs a new emotional trigger, not just a new format.

## 2026-11-09 view (hook and hold, 30 days to 2026-11-09)

| Family | Spend | ROAS | CPA | Hook | Hold |
|---|---|---|---|---|---|
| 3D Pixar (Animation Ad + Pixar-Style VSL) | $67k | 0.79–0.82 | $66–69 | 49–51% | 26–34% |
| Song (Pixar-Style Song + Singing Animation) | $22k | 0.87–0.99 | $54–64 | 41–47% | 23–28% |
| Movie drama (Cinematic; Movie Scene AI just launched) | $5k | 0.67 | $79 | 53% | **37%** |
| Story VSL | $46k | 0.72 | $79 | 44% | 19% |
| Account, all ads | — | 0.83 | $67 | — | — |

What this says: the three story formats are the best in the account at **holding attention** (hold is
1.5–2× a normal VSL) and they carry a lot of spend. Their ROAS is at the account average, not above it.
So each beat map below keeps what earns the hold and adds what we think is missing at the sale end
(marked **Test**). Re-run these numbers monthly (`../what-sells.md`, "How to refresh") and promote or
drop the tests.

## What all three formats share

1. **The hook is a confrontation, not a question.** In every batch, Meta put almost all the spend on the
   most direct, most cruel hook: "tired of looking at your bald ass" (gymaffair), "My mama asked me to put
   my wig back on for my sister's wedding" (Lymphoria), "My mother-in-law said I should not wear my natural
   hair anymore and started laughing" (Christmas song), screaming at the motel door (pregnant-aunt). The
   soft or accidental versions of the same scene got almost nothing. Write 3 hooks; make at least one the
   blunt one.
2. **A person causes the pain**: a husband, a rival, a mother, a mother-in-law, a cop, a classmate.
   The viewer's anger at that person is what holds her for five minutes.
3. **The cure comes from a trusted woman**, never from an ad: an elder on a park bench, a gym friend,
   a cousin, a sister, a coworker, the clinic receptionist. The product comes out of *her* bag.
4. **Same mechanism every time**: it's not age or genetics, it's chronic scalp inflammation; the
   follicles are asleep, not dead; oils sit on top and can't reach it; two capsules work from the inside.
5. **Week-by-week timeline** (week 1–2 shedding stops, week 3–4 baby hairs, week 6–8 edges and crown).
6. **Status flip**: she walks back into the same room (the pool, the church, the wedding, the dinner)
   and the person who shamed her is the one who's speechless, or asks for the secret.
7. **On screen (four winners watched 2026-11-09):** big face close-ups with a cut every 2–3 s; the
   hair problem visible in the first frame; the real bottle shown once, in the mentor's hands; outline
   captions of 2–4 words (not the box); and **none of them ends on a clear offer card** (one has a faint
   see-through line of text). That's the first thing to test.
8. **Every one of these is remade from a competitor's winning ad** (the strategists find them on Atria,
   app.tryatria.com, or the Facebook Ad Library) and adapted to Black women and our mechanism. That is
   the job of the competitor research step.
