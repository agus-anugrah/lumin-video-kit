#!/usr/bin/env python3
"""Render timeline.json to an MP4 with ffmpeg (for review, or as the deliverable for CapCut editors).

Every visual is scaled to cover the frame and centre-cropped. Upper video tracks sit on top of lower
ones. Audio tracks are mixed with each clip's gain_db. Optionally burns in captions (.srt or .ass).

Usage: python3 scripts/render.py jobs/<job>/timeline/timeline.json --out jobs/<job>/renders/v1.mp4 \
          [--burn-captions] [--crf 18]
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline as tlmod  # noqa: E402


def esc_path(p: str) -> str:
    return p.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def ffmpeg_bin() -> str:
    """Homebrew's plain ffmpeg can't burn captions (no libass); its ffmpeg-full can, but is keg-only."""
    for p in (os.environ.get("LUMIN_FFMPEG"), "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
              "/usr/local/opt/ffmpeg-full/bin/ffmpeg"):
        if p and Path(p).exists():
            return p
    return "ffmpeg"


def has_subtitles_filter(ff: str) -> bool:
    out = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return any(line.split()[1:2] == ["subtitles"] for line in out.splitlines() if line.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline_json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--burn-captions", action="store_true")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--dry-run", action="store_true", help="print the ffmpeg command only")
    args = ap.parse_args()

    tl = tlmod.load(args.timeline_json)
    W, H, fps = tl["width"], tl["height"], tl["fps"]
    total = tlmod.duration(tl)
    inputs, filters = [], []
    base = "base"
    filters.append(f"color=c=black:s={W}x{H}:r={fps}:d={total:.3f}[{base}]")

    idx = 0
    for t, track in enumerate(tl["video"]):
        for c in sorted(track, key=lambda c: c["start"]):
            info = tlmod.probe(c["file"])
            dur = c["out"] - c["in"]
            if info["is_image"]:
                inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", c["file"]]
                trim = f"trim=duration={dur:.3f}"
            else:
                inputs += ["-i", c["file"]]
                trim = f"trim=start={c['in']:.3f}:end={c['out']:.3f}"
            lab = f"v{idx}"
            filters.append(
                f"[{idx}:v]{trim},setpts=PTS-STARTPTS+{c['start']:.3f}/TB,fps={fps},"
                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[{lab}]")
            nxt = f"o{idx}"
            filters.append(f"[{base}][{lab}]overlay=eof_action=pass:"
                           f"enable='between(t,{c['start']:.3f},{c['start'] + dur:.3f})'[{nxt}]")
            base = nxt
            idx += 1

    alabels = []
    for track in tl["audio"]:
        for c in sorted(track, key=lambda c: c["start"]):
            inputs += ["-i", c["file"]]
            lab = f"a{idx}"
            delay = int(round(c["start"] * 1000))
            filters.append(
                f"[{idx}:a]atrim=start={c['in']:.3f}:end={c['out']:.3f},asetpts=PTS-STARTPTS,"
                f"aresample=48000,aformat=channel_layouts=stereo,volume={c.get('gain_db', 0)}dB,"
                f"adelay={delay}|{delay}[{lab}]")
            alabels.append(f"[{lab}]")
            idx += 1

    ff = ffmpeg_bin()
    vout = base
    if args.burn_captions and tl.get("captions") and not has_subtitles_filter(ff):
        sys.exit("This ffmpeg can't burn in captions (built without libass).\n"
                 "Mac: brew install ffmpeg-full   (the kit finds it automatically)\n"
                 "Windows: winget install Gyan.FFmpeg   (the full build has it)\n"
                 "Or render without --burn-captions and import captions.srt in the editing app.")
    if args.burn_captions and tl.get("captions"):
        filters.append(f"[{base}]subtitles='{esc_path(tl['captions'])}'[vsub]")
        vout = "vsub"
    maps = ["-map", f"[{vout}]"]
    if alabels:
        filters.append(f"{''.join(alabels)}amix=inputs={len(alabels)}:normalize=0:duration=longest[aout]")
        maps += ["-map", "[aout]"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ([ff, "-y", "-hide_banner", "-loglevel", "warning"] + inputs
           + ["-filter_complex", ";".join(filters)] + maps
           + ["-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
              "-pix_fmt", "yuv420p", "-r", str(fps), "-c:a", "aac", "-b:a", "192k",
              "-movflags", "+faststart", str(out)])
    if args.dry_run:
        print(" ".join(f"'{a}'" if " " in a or ";" in a else a for a in cmd))
        return
    subprocess.run(cmd, check=True)
    print(f"{out}  ({total:.1f}s)")


if __name__ == "__main__":
    main()
