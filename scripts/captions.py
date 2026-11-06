#!/usr/bin/env python3
"""Captions from a word-level transcript, split by meaning into short cards.

Rules (see presets/captions.md): 1-4 words per card, at most ~22 characters, break at punctuation
and pauses, never end a card on a small word (a, the, to, my...), never split a number from its unit.

Usage:
  python3 scripts/captions.py jobs/<job>/transcript/words.json --out jobs/<job>/captions/captions \
      [--cutlist jobs/<job>/cuts/cutlist.json] [--max-words 4] [--max-chars 22] [--upper]
Writes captions.srt (for Premiere caption tracks / CapCut import) and captions.ass (burn-in, with
the spoken word highlighted, styled from presets/captions.md defaults).
--cutlist maps source times onto the cut timeline and drops words that were cut.
"""
import argparse
import json
import re
from pathlib import Path

WEAK_END = {"a", "an", "the", "to", "of", "and", "or", "but", "my", "your", "her", "his", "our", "their",
            "i", "in", "on", "at", "for", "with", "is", "was", "it's", "that", "so", "if", "from", "by",
            "as", "this", "these", "those", "be", "not", "no", "can", "will", "just"}


def clean(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def remap(words, cutlist):
    """Source time -> timeline time; words outside kept ranges are dropped."""
    out, offset = [], 0.0
    for r in cutlist["keep"]:
        for w in words:
            mid = (w["start"] + w["end"]) / 2
            if r["in"] <= mid <= r["out"]:
                out.append({"word": w["word"],
                            "start": round(max(w["start"], r["in"]) - r["in"] + offset, 3),
                            "end": round(min(w["end"], r["out"]) - r["in"] + offset, 3)})
        offset += r["out"] - r["in"]
    return out


def chunk(words, max_words, max_chars):
    cards, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["word"] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = (nxt["start"] - w["end"]) if nxt else 9
        punct = bool(re.search(r"[.,!?;:—]$", w["word"]))
        too_long = nxt and len(text) + 1 + len(nxt["word"]) > max_chars
        full = len(cur) >= max_words
        if nxt is None or punct or pause > 0.3 or full or too_long:
            # don't end on a weak word if the next word can join this card or start the next
            if nxt and clean(w["word"]) in WEAK_END and len(cur) > 1 and not punct:
                cur.pop()
                cards.append(cur)
                cur = [w]
                continue
            # keep numbers with the word after them ("30 days")
            if nxt and re.fullmatch(r"\$?\d[\d,.%]*", w["word"].strip(".,")) and not punct and len(cur) > 1:
                cur.pop()
                cards.append(cur)
                cur = [w]
                continue
            cards.append(cur)
            cur = []
    if cur:
        cards.append(cur)
    return [c for c in cards if c]


def srt_t(t):
    ms = int(round(max(t, 0) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_t(t):
    cs = int(round(max(t, 0) * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Card,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,6,0,2,90,90,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("words_json")
    ap.add_argument("--out", required=True, help="output path without extension")
    ap.add_argument("--cutlist")
    ap.add_argument("--max-words", type=int, default=4)
    ap.add_argument("--max-chars", type=int, default=22)
    ap.add_argument("--upper", action="store_true")
    ap.add_argument("--font", default="Montserrat ExtraBold")
    ap.add_argument("--size", type=int, default=78)
    ap.add_argument("--highlight", default="&H0000D7FF", help="ASS colour (BGR) of the spoken word")
    ap.add_argument("--margin-v", type=int, default=520, help="px from the bottom (keeps out of the UI)")
    args = ap.parse_args()

    words = json.loads(Path(args.words_json).read_text(encoding="utf-8"))["words"]
    if args.cutlist:
        words = remap(words, json.loads(Path(args.cutlist).read_text(encoding="utf-8")))
    cards = chunk(words, args.max_words, args.max_chars)

    def txt(w):
        s = w["word"].strip()
        return s.upper() if args.upper else s

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    srt = []
    for n, c in enumerate(cards, 1):
        end = c[-1]["end"]
        srt.append(f"{n}\n{srt_t(c[0]['start'])} --> {srt_t(end)}\n{' '.join(txt(w) for w in c)}\n")
    out.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")

    events = []
    for c in cards:
        for i, w in enumerate(c):
            start = w["start"] if i else c[0]["start"]
            end = c[i + 1]["start"] if i + 1 < len(c) else c[-1]["end"]
            parts = [("{\\c" + args.highlight + "&}" + txt(x) + "{\\c&H00FFFFFF&}") if j == i else txt(x)
                     for j, x in enumerate(c)]
            events.append(f"Dialogue: 0,{ass_t(start)},{ass_t(end)},Card,,0,0,0,,{' '.join(parts)}")
    out.with_suffix(".ass").write_text(
        ASS_HEAD.format(font=args.font, size=args.size, margin_v=args.margin_v) + "\n".join(events) + "\n",
        encoding="utf-8")
    print(f"{len(cards)} cards -> {out.with_suffix('.srt')} and .ass")


if __name__ == "__main__":
    main()
