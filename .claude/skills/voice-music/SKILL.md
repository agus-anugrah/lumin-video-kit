---
name: voice-music
description: Voiceover, voice matching, sound effects and music beds for Lumin ads, with ElevenLabs and Suno. Use for "make the VO", "pick a voice", "change her voice", "add music", "BGM", "sound effects", "SFX", or any audio generation or audio check.
---

# Voice and music

## Credits first
Every paid generation: say what you'll make, how many takes, and the cost, then wait for "go".
Always pass the number of generations explicitly; never use a tool's default count.
Full VO = at most 2 takes.

## Voiceover (ElevenLabs connector)
1. Read the script and the speaker in `job.md`. Lumin's speaker is usually a Black woman 35–60
   speaking American English: warm, real, a bit tired or emotional, never announcer-polished.
   An industry-expose script may have a hairstylist or expert voice: confident, plain.
2. List voices with filters (gender, age, accent, use case = conversational / social media), pick
   3 candidates, render the first line with each (1 generation each). The editor picks.
3. Render the full script with the chosen voice. Keep ElevenLabs' file name, add the job code in front.
   Save to `vo/`.
4. Transcribe the result for word timings: `python3 scripts/transcribe.py vo/<file> --out transcript`.
5. Listen for problems in the transcript: wrong words, "Lumin" or "Root Revive" mispronounced,
   swallowed endings. Fix by re-rendering only that line and replacing it in the edit.

Pronunciation: "Lumin" = LOO-min. "Root Revive" = root re-VIVE. "CCCA" = see-see-see-AY.
Add others to `rules.md` as you meet them.

## Voice match (talking heads)
When a talking-head clip's voice doesn't match the VO voice, run the ElevenLabs voice changer
(speech-to-speech) on the clip's audio with the VO voice id, keep timing, and use the matched audio
under the clip. Needs the editor's ElevenLabs key (`elevenlabs/skills` voice-changer skill).

## Sound effects (ElevenLabs)
Short and quiet. Typical: soft whoosh on hard cuts, small pop when a caption card or arrow lands,
gentle ding on the product reveal, low "wrong" tone for the problem side, room tone to fill gaps.
Peak around −15 dBFS under speech. Prefer the clip's own sound when it's clean.

## Music
Order: music goes in **after** the picture is locked, never inside B-roll clips.
- **ElevenLabs music** (hands-free): instrumental, describe mood + tempo + instruments, ask for the
  ad's length plus 5 s.
- **Suno** (when the editor or Salam wants Suno's sound): Suno asks for a captcha before generating,
  so the editor creates the song on suno.com (instrumental on). If the editor has the unofficial
  `suno` CLI signed in, you may use it only to list and download their takes. Never solve, skip or
  get around a captcha, and never use a tool's captcha solver.

Mood by angle: personal story / transformation → soft piano or warm R&B instrumental, slow build;
industry expose → low, serious pulse; offer → light, upbeat, not cheesy. Nothing with vocals.

Check every music file: `python3 scripts/vocals_check.py <file>` must PASS (no vocals). If it fails,
use the `no_vocals.wav` it made, or pick another take.

## Levels (presets/audio.json)
VO is king: dialogue around −16 LUFS before the master; music bed 20–24 dB under the voice with a
2 s fade out; final master −14 LUFS integrated, true peak ≤ −1 dBTP (`scripts/loudness.py`).
