# Song (Pixar-style singing ad)

Built 2026-11-09 from Amar's Lymphoria Crazy Winner ($18k, ROAS 0.89, hook 45%, hold 32%), Christmas Song
AI ($2.9k, ROAS 1.02; its first ad 1.59), Daniel's Batch 43 sunday-service-show ($1.3k, 0.80, hold 33%) and
Amar's AI Song Competitor's Winner (0.49). Lymphoria was remade from a competitor ad with 60,000+ likes.

**What it is:** the whole story VSL, **sung** as a soul ballad over Pixar-style 3D animation. The lyric is
the script almost word for word (it rhymes loosely or not at all); the song carries the emotion, the
animation shows each line. 2–4 minutes.

**Job:** cold traffic, problem or solution aware. Best ROAS of the three story formats right now.

## The 12 beats

| # | Beat | What happens | From the winners |
|---|---|---|---|
| 1 | **Family wound** (hook) | One or two lines: a family member or partner shames her about her hair, at a family event, in front of people. Then "Let me tell you how my family works." | "My mama asked me to put my wig back on for my sister's wedding. I'd just gotten my edges back." · "My mother-in-law said I should not wear my natural hair anymore and started laughing. In front of 14 people. My husband just kept cutting his turkey." |
| 2 | **Her role** | The part the family gave her: the older one in the wig, behind her sister in photos; "you got such a pretty face". | "That's the polite way of saying the rest of you isn't." |
| 3 | **It keeps happening** | The humiliation repeats at every gathering: Mother's Day, the niece's birthday, Easter in a wig. | — |
| 4 | **Everything failed** | Sung list: castor oil, rosemary, biotin for a year, minoxidil every night, a $1,000 salon treatment. | — |
| 5 | **Dismissed** | The doctor barely looks up: "just genetics, try a stronger shampoo." She cries in her car. | — |
| 6 | **The messenger** | A trusted woman with full hair: cousin Renee in Houston, coworker Zofia in her late 50s, sister Patricia, a 71-year-old clinic receptionist. | — |
| 7 | **One quotable truth** | The mechanism in a line people remember: "You can't moisturize inflammation. You gotta clear it." Follicles shut down, they don't die. | Lymphoria adds a Black trichologist (Dr. Michelle Davis) as authority |
| 8 | **The product** | Root Revive by Lumin, two capsules a day, from the inside. "I started the next morning. I didn't tell anyone." | — |
| 9 | **Week by week** | Week 2 the pillow is clean, week 4 baby hairs at the edges, week 6 the wig comes off at home. | — |
| 10 | **Back into the room** | She walks into the same family event with her real hair. The room goes quiet. The person who shamed her freezes, or later asks for the secret. | The mother-in-law in the kitchen: "What have you been doing?" |
| 11 | **Resolution** | The family heals: the sister apologises, mama's eyes are wet, a photo side by side. | "You couldn't tell which one was the pretty one." |
| 12 | **Offer + identity close** | "It's not your fault. It's inflammation." Root Revive, 60% off for first-time customers, 90-day guarantee, link below. A last line that hands it to her: "I was the one in the wig for 32 years, and the family survived. Your turn." | — |

## Hooks that won
Lymphoria Hook 3 (mama asking her to wear the wig) took 98% of spend over "My whole family turned on
me". Christmas Hook 2 (mother-in-law laughing, 14 people, husband cutting turkey) took almost all of it.
Sunday service Hook 2 (the ex brings the homewrecker to church). The winner names **who** did it, **what
they said about her hair**, and **who watched**.

## What the winner looks like on screen (Lymphoria Hook 3, watched frame by frame 2026-11-09)
5:00, 9:16, from the Lumin page; headline "Fill In Your Edges & Crown 🧡".
- 0:00 first frame: her at a lit vanity mirror, hair in a puff, the caption "My mama asked me" big in the
  middle. The hook is on screen from frame one.
- Pixar-style family film: Jasmine's long hair swinging (0:19), mama in green with grey hair at the
  engagement (0:45), her clutching her thin crown at night on "Minoxidil every night" (1:15).
- 1:45 **the mechanism is a realistic 3D medical cross-section** of a follicle ("They just shut down"),
  not a cartoon.
- 2:15 "Week four": **a realistic macro of a scalp with baby hairs**, cut into the cartoon. In the kit
  that shot must be real footage (B-roll library), never generated: it's a proof shot (CLAUDE.md rule 3).
- 3:13 the wedding dress at mama's house; 3:43 the reception with champagne; 4:13 the coffee-cup ending
  ("the pretty one"); 4:38 the bottle small at the bottom on "Two capsules a day"; 4:56 ends on her
  smiling face with long curly hair. **No offer card at the end.**
- Captions: white sentence case with a dark outline, 2–4 words, no colour. The lead reads 30s and pretty
  in the cartoon style, like the Pixar winner.

## Test
- The two best song ads both say the offer (60% off, 90-day guarantee, link below) in the last lines.
  Keep it; add an on-screen offer card under the last verse.
- Show the real bottle (composited) on the product line and the close.

## Production
- **Lyrics**: the script, cut into verses. Keep every product fact word for word.
- **Song (Suno, made by the editor on suno.com; Suno asks for a captcha):** soul / R&B ballad, a warm
  Black female lead vocal. Use only `[Verse]` tags so Suno doesn't add a chorus that repeats lines. No
  rap parts. Vocals from the first second: no long intro (Daniel's note: start where it gets going). The
  strategist may give a Suno reference link: match it. ElevenLabs music can also sing lyrics if the editor
  prefers it; ask first.
- The song **is** the voice: `vocals_check.py` doesn't apply. Transcribe the final song for word timings
  (`scripts/transcribe.py`) and cut each animated shot on its line.
- **Captions are the lyrics**, every word, in the default box style. Most people watch muted.
- Visuals: preset `presets/3d-animated.md`, one shot per lyric line, same cast sheets as the Pixar format.
  The singer is the lead character; she lip-syncs only in a few close-ups, the rest is story.
- Mechanism lines get the 3D follicle cutaway.
