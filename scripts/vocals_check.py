#!/usr/bin/env python3
"""Check that a music bed has no vocals (or count how loud they are) using Demucs.

Usage: python3 scripts/vocals_check.py <music file> [--out jobs/<job>/audio/demucs] [--limit -40]
Splits the track into vocals / no_vocals, measures the vocal stem, and prints PASS when vocals are
quieter than --limit LUFS (default -40, i.e. nothing you'd hear under a voiceover). On FAIL, the
no_vocals.wav it wrote can be used as the bed instead.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loudness import measure  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("music")
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=float, default=-40.0)
    args = ap.parse_args()

    src = Path(args.music).resolve()
    out = Path(args.out or src.parent / "demucs")
    subprocess.run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-o", str(out), str(src)],
                   check=True)
    stems = next(out.glob(f"*/{src.stem}"), None)
    if not stems:
        sys.exit(f"Demucs output not found under {out}")
    vocals = measure(str(stems / "vocals.wav"))
    v = float(vocals["input_i"]) if vocals["input_i"] not in ("-inf", "inf") else -99.0
    verdict = "PASS" if v < args.limit else "FAIL"
    print(f"{verdict}: vocal stem {v:.1f} LUFS (limit {args.limit}). Instrumental: {stems / 'no_vocals.wav'}")


if __name__ == "__main__":
    main()
