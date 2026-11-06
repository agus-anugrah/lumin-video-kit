#!/usr/bin/env python3
"""Word-level transcript of a video or audio file.

Uses WhisperX (better word timings) and falls back to faster-whisper if WhisperX isn't installed.

Usage: python3 scripts/transcribe.py <media> --out jobs/<job>/transcript [--model large-v3] [--lang en]
Writes:
  words.json      [{"word": "Every", "start": 1.23, "end": 1.51}, ...]
  transcript.txt  one line per segment: "[m:ss.s - m:ss.s] text"
  transcript.srt  plain segment subtitles (for reading, not the styled captions)
"""
import argparse
import json
import sys
from pathlib import Path


def fmt(t: float) -> str:
    m, s = divmod(max(t, 0.0), 60)
    return f"{int(m)}:{s:04.1f}"


def srt_time(t: float) -> str:
    ms = int(round(max(t, 0.0) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def pick_device():
    try:
        import torch  # noqa: F401
        if torch.cuda.is_available():
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def with_whisperx(media, model_name, lang):
    import whisperx

    device, compute = pick_device()
    audio = whisperx.load_audio(str(media))
    model = whisperx.load_model(model_name, device, compute_type=compute, language=lang)
    result = model.transcribe(audio, batch_size=8 if device == "cpu" else 16)
    language = result.get("language", lang or "en")
    align_model, meta = whisperx.load_align_model(language_code=language, device=device)
    aligned = whisperx.align(result["segments"], align_model, meta, audio, device,
                             return_char_alignments=False)
    segments, words = [], []
    for seg in aligned["segments"]:
        seg_words = []
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                seg_words.append({"word": w["word"].strip(), "start": round(w["start"], 3),
                                  "end": round(w["end"], 3)})
        words.extend(seg_words)
        segments.append({"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()})
    return segments, words, "whisperx"


def with_faster_whisper(media, model_name, lang):
    from faster_whisper import WhisperModel

    device, compute = pick_device()
    model = WhisperModel(model_name, device=device, compute_type=compute)
    segs, _info = model.transcribe(str(media), word_timestamps=True, vad_filter=True, language=lang)
    segments, words = [], []
    for seg in segs:
        for w in seg.words or []:
            words.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
        segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    return segments, words, "faster-whisper"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()

    media = Path(args.media).expanduser().resolve()
    if not media.exists():
        sys.exit(f"Not found: {media}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    try:
        segments, words, engine = with_whisperx(media, args.model, args.lang)
    except ImportError:
        print("WhisperX not installed, using faster-whisper.", file=sys.stderr)
        segments, words, engine = with_faster_whisper(media, args.model, args.lang)

    (out / "words.json").write_text(json.dumps({"source": str(media), "engine": engine, "words": words},
                                               indent=1), encoding="utf-8")
    (out / "transcript.txt").write_text(
        "\n".join(f"[{fmt(s['start'])} - {fmt(s['end'])}] {s['text']}" for s in segments) + "\n",
        encoding="utf-8")
    (out / "transcript.srt").write_text(
        "\n".join(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n"
                  for i, s in enumerate(segments, 1)), encoding="utf-8")
    print(f"{engine}: {len(words)} words, {len(segments)} segments -> {out}")


if __name__ == "__main__":
    main()
