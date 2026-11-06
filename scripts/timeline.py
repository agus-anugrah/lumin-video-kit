"""Shared helpers for timeline.json, used by xml_export.py, render.py and captions.py.

timeline.json format (all times in seconds):
{
  "name": "VS-312 church wig v1",
  "fps": 30, "width": 1080, "height": 1920,
  "video": [                         # tracks, V1 first; later tracks sit on top
    [ {"file": "/abs/clip.mp4", "in": 0.0, "out": 2.4, "start": 0.0}, ... ],
    [ {"file": "/abs/broll.mp4", "in": 0.0, "out": 3.0, "start": 1.2, "label": "shot 3"} ]
  ],
  "audio": [                         # A1 first
    [ {"file": "/abs/vo.wav", "in": 0.0, "out": 24.8, "start": 0.0, "gain_db": 0} ],
    [ {"file": "/abs/music.wav", "in": 0.0, "out": 26.0, "start": 0.0, "gain_db": -22} ]
  ],
  "captions": "/abs/captions.srt"    # optional, burned in by render.py --burn-captions
}
"""
import json
import subprocess
from functools import lru_cache
from pathlib import Path


def load(path):
    tl = json.loads(Path(path).read_text(encoding="utf-8"))
    tl.setdefault("fps", 30)
    tl.setdefault("width", 1080)
    tl.setdefault("height", 1920)
    tl.setdefault("video", [])
    tl.setdefault("audio", [])
    base = Path(path).resolve().parent
    for track in tl["video"] + tl["audio"]:
        for c in track:
            p = Path(c["file"]).expanduser()
            c["file"] = str(p if p.is_absolute() else (base / p).resolve())
    return tl


def duration(tl) -> float:
    end = 0.0
    for track in tl["video"] + tl["audio"]:
        for c in track:
            end = max(end, c["start"] + (c["out"] - c["in"]))
    return end


@lru_cache(maxsize=None)
def probe(file: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,channels,r_frame_rate",
         "-of", "json", file], capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {
        "duration": float(info.get("format", {}).get("duration") or 0),
        "has_video": v is not None,
        "has_audio": a is not None,
        "width": int(v["width"]) if v else 0,
        "height": int(v["height"]) if v else 0,
        "channels": int(a.get("channels", 2)) if a else 0,
        "is_image": Path(file).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"},
    }
