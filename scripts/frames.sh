#!/usr/bin/env bash
# Pull frames from a video so Claude can look at them.
# Usage: bash scripts/frames.sh <video> <out_dir> [count=8 | --fps 2]
#   count: that many frames spread evenly; --fps N: N frames per second (for checking AI clips).
set -euo pipefail
video="$1"; out="$2"; mode="${3:-8}"
mkdir -p "$out"
if [ "$mode" = "--fps" ]; then
  ffmpeg -hide_banner -loglevel error -y -i "$video" -vf "fps=${4:-2},scale=540:-2" "$out/f_%03d.jpg"
else
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$video")
  for i in $(seq 1 "$mode"); do
    t=$(awk -v d="$dur" -v i="$i" -v n="$mode" 'BEGIN{printf "%.2f", d*(i-0.5)/n}')
    ffmpeg -hide_banner -loglevel error -y -ss "$t" -i "$video" -frames:v 1 -vf "scale=540:-2" "$out/t_${t}.jpg"
  done
fi
ls "$out" | head -50
