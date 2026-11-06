# One-time setup of the Lumin video kit on Windows. Run from the kit folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
# Safe to run again; it skips what's already installed.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")
function Step($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Has($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") }

Step "Tools (ffmpeg, node, uv, git) via winget"
if (-not (Has winget)) { Write-Host "winget is missing: install 'App Installer' from the Microsoft Store, then run again."; exit 1 }
if (-not (Has ffmpeg)) { winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements }
if (-not (Has node))   { winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements }
if (-not (Has uv))     { winget install -e --id astral-sh.uv --accept-source-agreements --accept-package-agreements }
if (-not (Has git))    { winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements }
Refresh-Path

Step "Python tools for transcription and the vocals check (about 3 GB, takes a while)"
if (-not (Test-Path .venv)) { uv venv --python 3.11 .venv }
uv pip install --python .venv\Scripts\python.exe whisperx faster-whisper demucs
# Editors with an NVIDIA card: ask Agus to switch torch to the CUDA build for much faster transcripts.

Step "Higgsfield CLI"
if (-not (Has higgsfield)) { npm install -g @higgsfield/cli; Refresh-Path }
higgsfield account status *> $null
if ($LASTEXITCODE -ne 0) { higgsfield auth login }

Step "Premiere Pro bridge (only if Premiere is installed)"
$premiere = Get-ChildItem "C:\Program Files\Adobe" -Directory -Filter "Adobe Premiere Pro*" -ErrorAction SilentlyContinue
if ($premiere) {
  if (-not (Has premiere-pro-mcp)) { npm install -g adobe-premiere-pro-mcp; Refresh-Path }
  premiere-pro-mcp --install-cep
  premiere-pro-mcp --doctor
} else { Write-Host "Premiere not found, skipped. (CapCut editors don't need it.)" }

Step "Official skills: Higgsfield, ElevenLabs, HyperFrames"
npx -y skills add higgsfield-ai/skills
npx -y skills add elevenlabs/skills
npx -y hyperframes skills update

Step "ElevenLabs key (for sound effects, music and voice changer skills)"
$envFile = Join-Path $env:USERPROFILE ".elevenlabs\.env"
if (-not (Test-Path $envFile)) { npx -y @elevenlabs/cli@latest onboard connect --env-path $envFile }

Step "Check"
if (Has bash) { bash scripts/doctor.sh } else { Write-Host "Open Git Bash in this folder and run: bash scripts/doctor.sh" }
