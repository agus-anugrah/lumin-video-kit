#!/usr/bin/env python3
"""Create (or find) a job folder: jobs/<YYYY-MM-DD>-<slug>/ with job.md and the usual subfolders.

Usage: python3 scripts/new_job.py "VS 312 church wig" [--editor Name] [--batch "Salam Batch 312"]
Prints the job folder path.
"""
import argparse
import datetime as dt
import re
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SUBDIRS = ["source", "transcript", "cuts", "vo", "sheets", "stills", "clips", "audio", "graphics",
           "captions", "timeline", "renders", "review"]


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text[:60] or "job"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--editor", default="")
    ap.add_argument("--batch", default="")
    args = ap.parse_args()

    slug = slugify(args.name)
    jobs = KIT / "jobs"
    existing = sorted(jobs.glob(f"*-{slug}")) if jobs.exists() else []
    if existing:
        print(existing[-1])
        return

    folder = jobs / f"{dt.date.today().isoformat()}-{slug}"
    for sub in SUBDIRS:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    (folder / "job.md").write_text(
        f"# {args.name}\n\n"
        f"Editor: {args.editor or '?'}   Batch: {args.batch or '?'}   Ratio: ?   Preset: ?\n"
        f"Created: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        "## Brief\n\n(what the ad is, angle, who's on screen, length, never-show list)\n\n"
        "## Steps\n\n| Step | Status | Notes |\n|---|---|---|\n\n"
        "## Shots\n\n| # | Line (VO) | Shot | Secs | Status |\n|---|---|---|---|---|\n\n"
        "## Credits spent\n\n## Decisions and feedback\n",
        encoding="utf-8",
    )
    print(folder)


if __name__ == "__main__":
    main()
