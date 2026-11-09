# Lumin video kit

Claude makes and edits Lumin ads with you. Give it a script and it builds the whole AI ad: voiceover,
characters, storyboard, clips, captions, music and a first cut. Or give it real UGC footage and it
cuts it, captions it and puts it on your timeline. You approve the important steps (voice, characters,
storyboard, spending credits); Claude does the rest and checks its own work.

It runs in Claude Code on your computer and uses Lumin's accounts: Higgsfield for images and video,
ElevenLabs for voice, sound and music, HyperFrames for graphics, and Premiere Pro if you edit there.

## Setup (once, 20–40 minutes, mostly waiting)

1. Install **Claude Code** (or the Claude desktop app and use its Code tab) and sign in.
2. Get this folder (ask Agus for the link) and open a terminal in it.
3. Run the installer:
   - **Mac**: `bash scripts/setup-mac.sh`
   - **Windows** (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1`

   It installs ffmpeg, Node, the transcription tools, the Higgsfield CLI (and signs you in), the
   Premiere bridge if you have Premiere, and the official Higgsfield, ElevenLabs and HyperFrames skills.
4. In claude.ai → Settings → Connectors, connect **ElevenLabs** and **Figma** with the Lumin accounts.
5. **Premiere editors**: restart Premiere, open a project, then Window → Extensions →
   **MCP Bridge (CEP)** → Start Bridge.
6. Open this folder in Claude Code and say: **"Run the doctor and tell me what's missing."**

## Using it

Talk normally. Examples:

> Make the ad for VS batch 312. Brief: personal story, church wig moment, 9:16, 35 seconds.
> Script: (paste)

> I need B-roll for lines 3–5 of this script: (paste)

> Rough cut this UGC: /Users/me/Downloads/creator_take2.mp4. Cut hard, keep the emotion.

> Captions for this video, yellow highlight, then put it in my Premiere sequence VS-312-A.

> Red arrow on her edges at 0:04 and a green check on the bottle at 0:21.

Claude always tells you the credit cost and waits for "go" before generating.

## What's in the folder

| Path | What it is |
|---|---|
| `CLAUDE.md` | Claude's rules for Lumin (product, no fake proof, real bottle only, ask before spending) |
| `.claude/skills/` | One skill per stage: `ai-ad`, `broll`, `rough-cut`, `voice-music`, `captions`, `graphics`, `premiere`, `finish`, plus `sell-check` |
| `playbook/what-sells.md` | What Lumin's winning ads do, the numbers, and why the flops flopped. Claude reads it before every ad |
| `scripts/` | Transcribe, cut list, captions, XML for Premiere, render, loudness, vocals check, frames, setup, doctor |
| `presets/` | Looks (`ugc-iphone`, `realistic-drama`, `ancient-story`, `3d-animated`), never-list, captions, graphics, audio and export specs. Salam owns these |
| `references/` | Real product photos and Salam's loved/hated examples |
| `graphics/templates/` | Approved graphics to reuse |
| `rules.md` | Team rules, one line each (Salam approves) |
| `jobs/` | Your jobs: shot lists, stills, clips, audio, renders, notes (stays on your computer) |
| `.mcp.json` | Connects Claude to Premiere |

The kit updates itself from the team copy each time you open it, so new rules and presets reach
everyone.

## Tools it uses

| Tool | For |
|---|---|
| Higgsfield (CLI + skills) | Stills and clips: Nano Banana, Seedream, Soul ID, Kling 4.0, Seedance 2.5, Veo |
| Figma Weave (connector) | Backup generator with Kling 4.0, Nano Banana, Veo |
| ElevenLabs (connector + skills) | Voiceover, transcription, voice match, sound effects, music |
| Suno | Music when you want Suno's sound (you make it on suno.com, Claude checks it) |
| WhisperX | Word-level transcripts for cuts and captions |
| Demucs | Checks music has no vocals |
| HyperFrames | Motion graphics and overlays |
| Premiere Pro MCP | Puts edits, captions and graphics on your Premiere timeline |
| ffmpeg | Renders, frame checks, loudness |
