#!/usr/bin/env python3
"""Find what to cut in talking footage from a word-level transcript.

Removes long pauses, filler words (um, uh, ...) and retakes (the speaker restarts the same phrase:
the earlier attempt is cut, the last one kept). Cuts only ever happen in the gap between two words,
never inside a word.

Usage:
  python3 scripts/cutlist.py jobs/<job>/transcript/words.json --out jobs/<job>/cuts \
      [--max-pause 0.35] [--pad 0.06] [--no-retakes] [--keep-fillers]
Writes cuts/cutlist.json (keep + removed ranges, source seconds), cuts/cutlist.md (readable),
and cuts/timeline.json (V1 + A1 of the source, ready for xml_export.py or render.py).

Claude: always read cutlist.md against the transcript before using it. The retake finder is simple
and can be wrong; edit cutlist.json by hand when it is.
"""
import argparse
import json
import re
from pathlib import Path

FILLERS = {"um", "uh", "erm", "er", "hmm", "mm", "uhm", "umm", "ah"}


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def find_retakes(words, min_len=3, window=12.0):
    """Indexes of words in an abandoned attempt: a run of >= min_len words that is repeated
    (same normalised words) starting within `window` seconds after it."""
    drop = set()
    n = len(words)
    i = 0
    while i < n:
        best = None
        for j in range(i + min_len, n):
            if words[j]["start"] - words[i]["start"] > window:
                break
            k = 0
            while j + k < n and i + k < j and norm(words[i + k]["word"]) == norm(words[j + k]["word"]):
                k += 1
            if k >= min_len:
                best = j  # restart found: drop i..j-1 (the attempt plus anything said before the restart)
                break
        if best is not None:
            drop.update(range(i, best))
            i = best
        else:
            i += 1
    return drop


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("words_json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-pause", type=float, default=0.35, help="longest silence kept inside a take (s)")
    ap.add_argument("--pad", type=float, default=0.06, help="air kept before/after words (s)")
    ap.add_argument("--no-retakes", action="store_true")
    ap.add_argument("--keep-fillers", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()

    data = json.loads(Path(args.words_json).read_text(encoding="utf-8"))
    words = data["words"]
    source = data["source"]

    reasons = {}
    if not args.keep_fillers:
        for i, w in enumerate(words):
            if norm(w["word"]) in FILLERS:
                reasons[i] = "filler"
    if not args.no_retakes:
        for i in find_retakes(words):
            reasons.setdefault(i, "retake")

    # Build keep ranges from kept words, splitting at long pauses and at removed words.
    keep, removed = [], []
    cur = None
    for i, w in enumerate(words):
        if i in reasons:
            removed.append({"in": w["start"], "out": w["end"], "reason": reasons[i], "text": w["word"]})
            if cur:
                keep.append(cur)
                cur = None
            continue
        if cur and w["start"] - cur["last_end"] > args.max_pause:
            keep.append(cur)
            removed.append({"in": cur["last_end"], "out": w["start"], "reason": "pause",
                            "text": f"{w['start'] - cur['last_end']:.2f}s"})
            cur = None
        if cur is None:
            cur = {"first_start": w["start"], "last_end": w["end"], "words": [w["word"]]}
        else:
            cur["last_end"] = w["end"]
            cur["words"].append(w["word"])
    if cur:
        keep.append(cur)

    # Pad each range into the surrounding gaps without touching neighbouring words.
    starts = [w["start"] for w in words]
    ends = [w["end"] for w in words]
    ranges = []
    for k in keep:
        prev_end = max([e for e in ends if e <= k["first_start"]], default=0.0)
        next_start = min([s for s in starts if s >= k["last_end"]], default=k["last_end"] + 1.0)
        a = max(k["first_start"] - args.pad, (prev_end + k["first_start"]) / 2, 0.0)
        b = min(k["last_end"] + args.pad, (k["last_end"] + next_start) / 2)
        ranges.append({"in": round(a, 3), "out": round(b, 3), "text": " ".join(k["words"])})

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "cutlist.json").write_text(json.dumps({"source": source, "keep": ranges, "removed": removed},
                                                 indent=1), encoding="utf-8")

    total_src = words[-1]["end"] if words else 0
    total_keep = sum(r["out"] - r["in"] for r in ranges)
    lines = [f"# Cut list: {Path(source).name}", "",
             f"Kept {total_keep:.1f}s of {total_src:.1f}s in {len(ranges)} pieces.", "",
             "## Kept", ""]
    lines += [f"{n}. {r['in']:.2f}–{r['out']:.2f}  {r['text']}" for n, r in enumerate(ranges, 1)]
    lines += ["", "## Removed", ""]
    lines += [f"- {r['in']:.2f}–{r['out']:.2f}  {r['reason']}: {r['text']}" for r in removed]
    (out / "cutlist.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    t = 0.0
    v1, a1 = [], []
    for r in ranges:
        clip = {"file": source, "in": r["in"], "out": r["out"], "start": round(t, 3)}
        v1.append(dict(clip))
        a1.append(dict(clip))
        t += r["out"] - r["in"]
    timeline = {"name": Path(source).stem + " rough cut", "fps": args.fps, "width": 1080, "height": 1920,
                "video": [v1], "audio": [a1]}
    (out / "timeline.json").write_text(json.dumps(timeline, indent=1), encoding="utf-8")
    print(f"Kept {total_keep:.1f}s of {total_src:.1f}s; {len(removed)} cuts -> {out}")


if __name__ == "__main__":
    main()
