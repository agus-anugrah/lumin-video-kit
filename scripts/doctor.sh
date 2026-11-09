#!/usr/bin/env bash
# Checks that this computer is ready for the Lumin video kit.  bash scripts/doctor.sh
cd "$(dirname "$0")/.."
ok=1
good() { echo "OK      $1"; }
bad()  { echo "MISSING $1  -> $2"; ok=0; }
info() { echo "INFO    $1"; }
check() { if command -v "$1" >/dev/null 2>&1; then good "$1"; else bad "$1" "$2"; fi; }

check claude     "install Claude Code (or use the Claude desktop app, Code tab)"
check node       "run the setup script"
check ffmpeg     "run the setup script"
check higgsfield "npm install -g @higgsfield/cli"

if command -v higgsfield >/dev/null 2>&1; then
  if higgsfield account status >/dev/null 2>&1; then good "higgsfield signed in"
  else bad "higgsfield sign-in" "higgsfield auth login"; fi
fi

PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python.exe
if [ -x "$PY" ]; then
  "$PY" -c "import whisperx" 2>/dev/null && good "whisperx" || \
    { "$PY" -c "import faster_whisper" 2>/dev/null && info "faster-whisper only (whisperx missing, transcripts still work)" || bad "transcription" "run the setup script"; }
  "$PY" -c "import demucs" 2>/dev/null && good "demucs (vocals check)" || bad "demucs" "run the setup script"
else
  bad "Python tools (.venv)" "run the setup script"
fi

if command -v premiere-pro-mcp >/dev/null 2>&1; then good "premiere-pro-mcp (start the bridge in Premiere: Window > Extensions > MCP Bridge (CEP))"
else info "no Premiere bridge (fine for CapCut editors)"; fi

found() { ls -d "$HOME/.claude/skills/$1" ".claude/skills/$1" "$HOME/.agents/skills/$1" ".agents/skills/$1" >/dev/null 2>&1; }
found higgsfield-generate && good "Higgsfield skills" || bad "Higgsfield skills" "npx skills add higgsfield-ai/skills"
found text-to-speech      && good "ElevenLabs skills" || info "ElevenLabs skills not found (npx skills add elevenlabs/skills)"
found hyperframes         && good "HyperFrames skills" || info "HyperFrames skills not found (npx hyperframes skills update)"
[ -f "$HOME/.lumin-kit/session.json" ] && good "Lumin app login (your batches)" || bad "Lumin app login" "python3 scripts/lumin_batch.py login  (in your own terminal)"
[ -f "$HOME/.elevenlabs/.env" ] && good "ElevenLabs key" || info "no ElevenLabs key yet (only needed for SFX, music, voice changer)"

n=$(find references/product -type f ! -name '.*' 2>/dev/null | wc -l | tr -d ' ')
info "$n product photo(s) in references/product (product shots need them)"
n=$(find references/style/loved -type f ! -name '.*' 2>/dev/null | wc -l | tr -d ' ')
info "$n loved style example(s) in references/style/loved"

[ $ok = 1 ] && echo "Ready." || echo "Fix the MISSING lines above, then run this again."
