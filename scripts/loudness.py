#!/usr/bin/env python3
"""Measure or normalise loudness (EBU R128) with ffmpeg.

Usage:
  python3 scripts/loudness.py measure <file>
  python3 scripts/loudness.py normalize <in> <out> [--target -14] [--tp -1]
Targets live in presets/audio.json. normalize is two-pass loudnorm (measure, then apply linearly).
Video is copied untouched when the input has video.
"""
import argparse
import json
import re
import subprocess
import sys


def measure(path, target=-14.0, tp=-1.0, lra=11.0):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
         f"loudnorm=I={target}:TP={tp}:LRA={lra}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    if not m:
        sys.exit(p.stderr[-2000:])
    return json.loads(m.group(0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["measure", "normalize"])
    ap.add_argument("inp")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--target", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.0)
    ap.add_argument("--lra", type=float, default=11.0)
    args = ap.parse_args()

    m = measure(args.inp, args.target, args.tp, args.lra)
    if args.mode == "measure":
        print(f"Integrated {m['input_i']} LUFS | true peak {m['input_tp']} dBTP | LRA {m['input_lra']} LU")
        return
    if not args.out:
        sys.exit("normalize needs an output path")
    af = (f"loudnorm=I={args.target}:TP={args.tp}:LRA={args.lra}:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-i", args.inp, "-af", af,
                    "-ar", "48000", "-c:v", "copy", args.out], check=True)
    after = measure(args.out, args.target, args.tp, args.lra)
    print(f"{args.inp}: {m['input_i']} -> {after['input_i']} LUFS, peak {after['input_tp']} dBTP -> {args.out}")


if __name__ == "__main__":
    main()
