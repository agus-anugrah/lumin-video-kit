#!/usr/bin/env python3
"""timeline.json -> FCP7 XML (xmeml v4) that Premiere Pro and DaVinci Resolve import as a sequence.

Usage: python3 scripts/xml_export.py jobs/<job>/timeline/timeline.json --out "<folder>/<VIDEO CODE>.xml"

Premiere: File > Import > the .xml (or MCP import_fcp_xml). Media is linked from its absolute path, so
keep source files where they are. Images (stills) are placed as still clips.
"""
import argparse
import sys
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline as tlmod  # noqa: E402


def frames(sec: float, fps: int) -> int:
    return int(round(sec * fps))


def rate(fps: int) -> str:
    return f"<rate><timebase>{fps}</timebase><ntsc>FALSE</ntsc></rate>"


class Files:
    def __init__(self, fps):
        self.fps = fps
        self.ids = {}

    def ref(self, path: str) -> str:
        if path in self.ids:
            return f'<file id="{self.ids[path]}"/>'
        fid = f"file-{len(self.ids) + 1}"
        self.ids[path] = fid
        info = tlmod.probe(path)
        dur = frames(info["duration"] or 10.0, self.fps)
        media = ""
        if info["has_video"]:
            media += ("<video><samplecharacteristics>"
                      f"<width>{info['width']}</width><height>{info['height']}</height>"
                      "</samplecharacteristics></video>")
        if info["has_audio"]:
            media += (f"<audio><samplecharacteristics><samplerate>48000</samplerate>"
                      f"<depth>16</depth></samplecharacteristics>"
                      f"<channelcount>{info['channels']}</channelcount></audio>")
        posix = Path(path).as_posix()  # Windows: C:/Users/... ; Mac: /Users/...
        url = "file://localhost" + quote(posix if posix.startswith("/") else "/" + posix)
        return (f'<file id="{fid}"><name>{escape(Path(path).name)}</name>'
                f"<pathurl>{escape(url)}</pathurl>{rate(self.fps)}<duration>{dur}</duration>"
                f"<media>{media}</media></file>")


def clipitem(c, n, kind, files, fps):
    start = frames(c["start"], fps)
    end = start + frames(c["out"] - c["in"], fps)
    info = tlmod.probe(c["file"])
    src_in = 0 if info["is_image"] else frames(c["in"], fps)
    src_out = src_in + (end - start)
    name = escape(c.get("label") or Path(c["file"]).name)
    extra = ""
    if kind == "audio" and c.get("gain_db"):
        gain = 10 ** (c["gain_db"] / 20)
        extra = ("<filter><effect><name>Audio Levels</name><effectid>audiolevels</effectid>"
                 "<effectcategory>audiolevels</effectcategory><effecttype>audiolevels</effecttype>"
                 "<mediatype>audio</mediatype><parameter><parameterid>level</parameterid>"
                 f"<name>Level</name><value>{gain:.4f}</value></parameter></effect></filter>")
    return (f'<clipitem id="{kind}-{n}"><name>{name}</name><enabled>TRUE</enabled>'
            f"<duration>{frames(info['duration'] or 10.0, fps)}</duration>{rate(fps)}"
            f"<start>{start}</start><end>{end}</end><in>{src_in}</in><out>{src_out}</out>"
            f"{files.ref(c['file'])}"
            + (f"<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>"
               if kind == "audio" else "")
            + f"{extra}</clipitem>")


def build(tl) -> str:
    fps = tl["fps"]
    files = Files(fps)
    total = frames(tlmod.duration(tl), fps)
    n = 0
    vtracks = []
    for track in tl["video"]:
        items = []
        for c in sorted(track, key=lambda c: c["start"]):
            n += 1
            items.append(clipitem(c, n, "video", files, fps))
        vtracks.append(f"<track>{''.join(items)}</track>")
    atracks = []
    for track in tl["audio"]:
        items = []
        for c in sorted(track, key=lambda c: c["start"]):
            n += 1
            items.append(clipitem(c, n, "audio", files, fps))
        atracks.append(f"<track>{''.join(items)}</track>")
    fmt = ("<format><samplecharacteristics>"
           f"{rate(fps)}<width>{tl['width']}</width><height>{tl['height']}</height>"
           "<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4">'
            f'<sequence id="sequence-1"><name>{escape(tl["name"])}</name><duration>{total}</duration>'
            f"{rate(fps)}<media><video>{fmt}{''.join(vtracks)}</video>"
            f"<audio>{''.join(atracks)}</audio></media></sequence></xmeml>\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline_json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    tl = tlmod.load(args.timeline_json)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(tl), encoding="utf-8")
    print(f"{out}  ({tlmod.duration(tl):.1f}s, {len(tl['video'])} video / {len(tl['audio'])} audio tracks)")


if __name__ == "__main__":
    main()
