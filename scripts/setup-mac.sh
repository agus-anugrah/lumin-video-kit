#!/usr/bin/env bash
# One-time setup of the Lumin video kit on a Mac. Run from the kit folder:  bash scripts/setup-mac.sh
# Safe to run again; it skips what's already installed.
set -uo pipefail
cd "$(dirname "$0")/.."
step() { printf "\n== %s\n" "$1"; }

step "Homebrew tools (ffmpeg, node, uv, git)"
if ! command -v brew >/dev/null; then
  echo "Install Homebrew first: https://brew.sh  then run this script again."; exit 1
fi
for p in ffmpeg node uv git; do command -v "$p" >/dev/null || brew install "$p"; done
# The plain ffmpeg can't burn in captions; ffmpeg-full can (render.py finds it on its own).
brew list ffmpeg-full >/dev/null 2>&1 || brew install ffmpeg-full

step "Python tools for transcription and the vocals check (about 3 GB, takes a while)"
[ -d .venv ] || uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python whisperx faster-whisper demucs

step "Higgsfield CLI"
command -v higgsfield >/dev/null || npm install -g @higgsfield/cli
higgsfield account status >/dev/null 2>&1 || higgsfield auth login

step "Premiere Pro bridge (only if Premiere is installed)"
if ls /Applications | grep -qi "premiere"; then
  command -v premiere-pro-mcp >/dev/null || npm install -g adobe-premiere-pro-mcp
  premiere-pro-mcp --install-cep
  premiere-pro-mcp --doctor || true
else
  echo "Premiere not found, skipped. (CapCut editors don't need it.)"
fi

step "Official skills: Higgsfield, ElevenLabs, HyperFrames"
npx -y skills add higgsfield-ai/skills
npx -y skills add elevenlabs/skills
npx -y hyperframes skills update

step "ElevenLabs key (for sound effects, music and voice changer skills)"
if [ ! -f "$HOME/.elevenlabs/.env" ]; then
  npx -y @elevenlabs/cli@latest onboard connect --env-path "$HOME/.elevenlabs/.env" || \
    echo "Skipped. Run it later, or ask Agus for the steps."
fi

step "Check"
bash scripts/doctor.sh
