#!/usr/bin/env python3
"""A song-led AI ad (Song / 3D formats, the AI Commerce route) -> timeline.json, a Premiere sequence (XML), captions as SRT,
and a clean review video. Captions are NOT burned in: the editor adds them in Premiere (SRT -> caption track) in the
team's normal style. Burn them only when someone asks (--burn).

Input: <job>/edit.json
{
  "name": "GymCrown",                         # sequence / file name
  "song": "music/song_1.mp3",                 # the picked song (paths relative to the job)
  "lyrics": "music/lyrics.txt",               # the sung lyrics, [Verse] tags allowed
  "words": "music/song_1_words.json",         # transcript of the song with word timings (scripts/transcribe.py)
  "end": 105.6,                               # where the film ends (default: song length)
  "sections": [                               # one per shot, in order, on the song's clock
    {"id": "s01a", "start": 0.0, "end": 8.5, "file": "clips/s01a.mp4"},
    {"id": "s09",  "start": 83.8, "end": 87.2, "file": "stills/s09d.jpg"}   # a still is placed as a still clip
  ]
}

Usage:
  python3 scripts/song_timeline.py jobs/<job>            # timeline + XML + SRT + clean review MP4
  python3 scripts/song_timeline.py jobs/<job> --no-review
  python3 scripts/song_timeline.py jobs/<job> --burn     # review MP4 with the captions burned in (only on request)
Then in Premiere: File > Import > timeline/<name>.xml, and the `premiere` skill for the captions (import the SRT, make a
caption track, apply the Lumin style)."""
import argparse, difflib, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())


def probe_duration(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True, check=True).stdout.strip() or 0)


def lyric_words(lyrics):
    words = []
    for line in Path(lyrics).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("["):
            words += line.split()
    return words


def aligned_words(lyrics, words_json, end):
    """The lyrics word for word, each timed from the transcript (it mishears sung words; the lyrics are what's shown).
    Words the transcript missed get times between their neighbours; words before the first match start at the vocal."""
    lw = [{"word": w} for w in lyric_words(lyrics)]
    tw = json.loads(Path(words_json).read_text(encoding="utf-8"))
    tw = tw["words"] if isinstance(tw, dict) else tw
    tw = [(w[0], w[1], w[2]) if isinstance(w, list) else (w["start"], w["end"], w["word"]) for w in tw]
    a = [norm(x["word"]) for x in lw]; b = [norm(x[2]) for x in tw]
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            lw[blk.a + k]["start"], lw[blk.a + k]["end"] = tw[blk.b + k][0], tw[blk.b + k][1]
    known = [i for i, x in enumerate(lw) if "start" in x]
    if not known: sys.exit("No lyric word matched the transcript: check the song and lyrics files.")
    for i, x in enumerate(lw):
        if "start" in x: continue
        prev = max([k for k in known if k < i], default=None); nxt = min([k for k in known if k > i], default=None)
        if prev is None:
            span = lw[nxt]["start"] - tw[0][0]; x["start"] = tw[0][0] + span * i / nxt; x["end"] = x["start"] + span / nxt
        elif nxt is not None:
            span = lw[nxt]["start"] - lw[prev]["end"]; n = nxt - prev
            x["start"] = lw[prev]["end"] + span * (i - prev) / n; x["end"] = x["start"] + span / n
    return [{"word": x["word"], "start": round(x["start"], 3), "end": round(x["end"], 3)} for x in lw if "start" in x and x["start"] < end - 0.2]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job"); ap.add_argument("--no-review", action="store_true"); ap.add_argument("--burn", action="store_true")
    a = ap.parse_args()
    job = Path(a.job).resolve(); e = json.loads((job / "edit.json").read_text(encoding="utf-8"))
    song = job / e["song"]; end = float(e.get("end") or probe_duration(song)); name = e.get("name", job.name)
    (job / "timeline").mkdir(exist_ok=True); (job / "captions").mkdir(exist_ok=True); (job / "renders").mkdir(exist_ok=True)

    # 1. picture on V1 on the song's clock; a clip shorter than its section is held on its last frame by a still of it
    v1 = []
    for s in e["sections"]:
        f = job / s["file"]; need = round(s["end"] - s["start"], 3)
        if not f.exists(): sys.exit(f"{s['id']}: missing {f}")
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            v1.append({"file": str(f), "in": 0.0, "out": need, "start": s["start"], "label": s["id"]}); continue
        have = probe_duration(f); use = min(have, need)
        v1.append({"file": str(f), "in": 0.0, "out": round(use, 3), "start": s["start"], "label": s["id"]})
        if need - use > 0.04:                                   # hold: the clip's last frame as a still
            hold = job / "timeline" / f"{s['id']}_hold.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.1", "-i", str(f), "-frames:v", "1", "-update", "1", str(hold)], check=True)
            v1.append({"file": str(hold), "in": 0.0, "out": round(need - use, 3), "start": round(s["start"] + use, 3), "label": s["id"] + " hold"})
    tl = {"name": name, "fps": 30, "width": 1080, "height": 1920, "video": [v1],
          "audio": [[{"file": str(song), "in": 0.0, "out": end, "start": 0.0, "gain_db": 0}]]}

    # 2. captions: lyric words timed to the song -> SRT (Premiere caption track); never burned unless --burn
    words = aligned_words(job / e["lyrics"], job / e["words"], end)
    (job / "captions" / "words.json").write_text(json.dumps({"source": str(song), "engine": "lyrics+transcript", "words": words}, indent=1), encoding="utf-8")
    subprocess.run([sys.executable, str(HERE / "captions.py"), str(job / "captions" / "words.json"), "--out", str(job / "captions" / "captions"),
                    "--max-words", "4", "--upper"], check=True)
    tl["captions"] = str(job / "captions" / "captions.srt")
    tlp = job / "timeline" / "timeline.json"; tlp.write_text(json.dumps(tl, indent=1), encoding="utf-8")

    # 3. Premiere / Resolve sequence
    xml = job / "timeline" / f"{name}.xml"
    subprocess.run([sys.executable, str(HERE / "xml_export.py"), str(tlp), "--out", str(xml)], check=True)

    # 4. clean review video (captions only with --burn)
    if not a.no_review:
        out = job / "renders" / f"{name}_review{'_captions' if a.burn else ''}.mp4"
        cmd = [sys.executable, str(HERE / "render.py"), str(tlp), "--out", str(out)] + (["--burn-captions"] if a.burn else [])
        subprocess.run(cmd, check=True)
        print("review:", out)
    print("timeline:", tlp); print("Premiere XML:", xml); print("captions (SRT for Premiere):", job / "captions" / "captions.srt")


if __name__ == "__main__":
    main()
