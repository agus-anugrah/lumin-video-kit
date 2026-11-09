#!/usr/bin/env python3
"""Read your batches from the Lumin app (read-only), with your own app login.

  python3 scripts/lumin_batch.py login                 # once, in your own terminal (asks for your password)
  python3 scripts/lumin_batch.py whoami
  python3 scripts/lumin_batch.py mine [--all]          # your open batches (--all: every stage)
  python3 scripts/lumin_batch.py get 3946              # batch by code (or part of its name): brief, hooks,
                                                       # script, files -> a job folder; prints its path;
                                                       # then runs `research` for it (--no-research to skip)
  python3 scripts/lumin_batch.py research 3946         # competitors' top ads + ours around the batch's date
                                                       # -> <job>/research/ (research.md, videos, frames)
  python3 scripts/lumin_batch.py broll church wig      # search the app's B-roll library
  python3 scripts/lumin_batch.py broll-get <id> --out jobs/<job>/source   # download one clip

You only ever see what you can see in the app (the app's own access rules apply). Nothing is changed in
the app. Your password is never stored or shown: the login keeps a session token in
~/.lumin-kit/session.json (only your user can read it). `logout` deletes it.
"""
import argparse
import datetime
import getpass
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SUPABASE_URL = "https://smfkwamzbgjpuwrrjmaf.supabase.co"
# The app's publishable key: public by design (the website ships it to every browser). Access is decided
# by the signed-in user's role, not by this key.
PUBLISHABLE_KEY = "sb_publishable_2k9NV-9grSn3P_-4vE8Dyg_xkAUn-lR"
USERNAME_DOMAIN = "lumin.internal"
APP_URL = "https://lumin-app-tau.vercel.app"
BROLL_BUCKET = "broll-library"
OPEN_STAGES = ["pending", "in_progress", "needs_review", "feedback_given", "working_on_revisions",
               "done_with_revisions"]
STAGE_NAMES = {"ideation": "Ideation", "pending": "Pending", "in_progress": "In progress",
               "needs_review": "Needs review", "feedback_given": "Feedback given",
               "working_on_revisions": "Working on revisions", "done_with_revisions": "Done with revisions",
               "ready_to_launch": "Ready to launch", "launched": "Launched", "archived": "Archived"}

KIT = Path(__file__).resolve().parent.parent
SESSION = Path.home() / ".lumin-kit" / "session.json"


# ---------- HTTP ----------

def http(method, url, body=None, token=None, headers=None, raw=False):
    h = {"apikey": PUBLISHABLE_KEY, "Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if body is not None:
        h["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
            return data if raw else (json.loads(data) if data else None)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise SystemExit(f"Lumin app said {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Can't reach the Lumin app ({e.reason}). Check your internet.")


# ---------- session ----------

def save_session(s):
    SESSION.parent.mkdir(parents=True, exist_ok=True)
    SESSION.write_text(json.dumps(s), encoding="utf-8")
    try:
        os.chmod(SESSION.parent, 0o700)
        os.chmod(SESSION, 0o600)
    except OSError:
        pass


def session_from(resp):
    return {"access_token": resp["access_token"], "refresh_token": resp["refresh_token"],
            "expires_at": int(resp.get("expires_at") or time.time() + int(resp.get("expires_in", 3600))),
            "user_id": resp["user"]["id"], "email": resp["user"].get("email")}


def token():
    if not SESSION.exists():
        raise SystemExit("Not signed in. In your own terminal run:  python3 scripts/lumin_batch.py login")
    s = json.loads(SESSION.read_text(encoding="utf-8"))
    if s["expires_at"] - time.time() < 120:
        resp = http("POST", f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
                    {"refresh_token": s["refresh_token"]})
        s = session_from(resp)
        save_session(s)
    return s["access_token"], s["user_id"]


def rest(table, params):
    tok, _ = token()
    q = urllib.parse.urlencode(params, doseq=True, safe="*,().:")
    return http("GET", f"{SUPABASE_URL}/rest/v1/{table}?{q}", token=tok)


# ---------- helpers ----------

def names(ids):
    ids = sorted({i for i in ids if i})
    if not ids:
        return {}
    rows = rest("profiles", {"select": "id,full_name", "id": f"in.({','.join(ids)})"})
    return {r["id"]: r["full_name"] for r in rows}


def doc_export_url(link):
    """Google Doc link -> plain-text export of just that tab (if the link names one)."""
    m = re.search(r"docs\.google\.com/document/d/([A-Za-z0-9_-]+)", link or "")
    if not m:
        return None
    url = f"https://docs.google.com/document/d/{m.group(1)}/export?format=txt"
    tab = re.search(r"[?&#]tab=(t\.[A-Za-z0-9]+)", link)
    return url + (f"&tab={tab.group(1)}" if tab else "")


def fetch_doc(link):
    url = doc_export_url(link)
    if not url:
        return None, "not a Google Doc link"
    req = urllib.request.Request(url, headers={"User-Agent": "lumin-video-kit"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8-sig", errors="replace")
    except urllib.error.HTTPError as e:
        return None, f"Google said {e.code}"
    if text.lstrip().lower().startswith("<!doctype html") or "<html" in text[:500].lower():
        return None, "the doc isn't shared by link (open it with the Google Drive connector instead)"
    return text.replace("\r\n", "\n"), None


def find_batch(ref):
    cols = ("id,code,name,stage,format,brief_angle,awareness,funnel_stage,audience,problems,concept,pov,"
            "condition,headline_1,headline_2,ad_details_1,ad_details_2,ad_details_3,page_details,ad_url,"
            "ad_url_type,launch_date,script_link,files_link,strategist_id,editor_id,is_priority,updated_at")
    if str(ref).isdigit():
        rows = rest("batches", {"select": cols, "code": f"eq.{ref}"})
    else:
        rows = rest("batches", {"select": cols, "name": f"ilike.*{ref}*", "order": "updated_at.desc",
                                "limit": "10"})
    if not rows:
        raise SystemExit(f"No batch found for '{ref}' (or you can't see it in the app).")
    if len(rows) > 1:
        print("More than one batch matches; use the code:")
        for r in rows:
            print(f"  {r['code']}  {r['name']}  ({STAGE_NAMES.get(r['stage'], r['stage'])})")
        raise SystemExit(1)
    return rows[0]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50]


# The app's format labels -> the kit's format families (playbook/formats/README.md). First match wins,
# so "Pixar-Style Song" is a song and "AI Pixar VSL" is Pixar. Add new labels here and in the README.
FAMILIES = [
    ("song", "Song", "playbook/formats/song.md", ("song", "singing")),
    ("movie-drama", "Movie drama", "playbook/formats/movie-drama.md", ("movie", "cinematic", "cinema", "drama")),
    ("pixar", "3D Pixar", "playbook/formats/pixar.md", ("pixar", "animation", "animated", "3d")),
    ("sale", "Sale", "playbook/what-sells.md (sale ad)", ("sale",)),
    ("static", "Static", "not a video", ("static",)),
    ("vsl", "Story VSL", "playbook/what-sells.md (12-beat VSL)",
     ("vsl", "podcast", "voiceover", "voice over", "b-roll", "talking head", "ugc", "transformation", "personal")),
]
SCRIPT_FORMAT_LINE = re.compile(r"(?:format(?:/style)?|ad format)\s*[:\n\t]+\s*([^\n]{2,60})", re.I)


def format_family(app_format, script_text=""):
    """(family key, label, beat map, where it came from) for a batch, or None when nothing matches."""
    candidates = [(app_format, "the app's format")] if app_format else []
    m = SCRIPT_FORMAT_LINE.search(script_text[:3000]) if script_text else None
    if m:
        candidates.append((m.group(1).strip(), "the script's header"))
    for value, source in candidates:
        low = value.lower()
        for key, label, beat_map, words in FAMILIES:
            if any(w in low for w in words):
                return key, label, beat_map, f'{source} "{value}"'
    return None


# ---------- commands ----------

def cmd_login(_):
    if not sys.stdin.isatty():
        raise SystemExit("Run login in your own terminal (it asks for your password, which Claude must not see).")
    login = input("Lumin app email or username: ").strip().lower()
    password = getpass.getpass("Password (hidden): ")
    email = login if "@" in login else f"{login}@{USERNAME_DOMAIN}"
    try:
        resp = http("POST", f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                    {"email": email, "password": password})
    except SystemExit as e:
        if "invalid_credentials" in str(e):
            raise SystemExit("That login and password don't match a Lumin app account. Same login as the app.")
        raise
    s = session_from(resp)
    save_session(s)
    me = names([s["user_id"]]).get(s["user_id"], email)
    print(f"Signed in as {me}. You can now ask Claude to show your batches.")


def cmd_logout(_):
    if SESSION.exists():
        SESSION.unlink()
    print("Signed out (session removed from this computer).")


def cmd_whoami(_):
    _, uid = token()
    rows = rest("profiles", {"select": "full_name,role", "id": f"eq.{uid}"})
    p = rows[0] if rows else {}
    print(f"{p.get('full_name', '?')} ({p.get('role', '?')})")


def cmd_mine(args):
    _, uid = token()
    params = {"select": "code,name,stage,format,launch_date,is_priority,updated_at,strategist_id",
              "or": f"(editor_id.eq.{uid},strategist_id.eq.{uid})", "order": "updated_at.desc", "limit": "50"}
    if not args.all:
        params["stage"] = f"in.({','.join(OPEN_STAGES)})"
    rows = rest("batches", params)
    if not rows:
        print("No open batches assigned to you." if not args.all else "No batches assigned to you.")
        return
    who = names(r["strategist_id"] for r in rows)
    order = {s: i for i, s in enumerate(["in_progress", "working_on_revisions", "feedback_given", "pending",
                                         "needs_review", "done_with_revisions"])}
    rows.sort(key=lambda r: (order.get(r["stage"], 99), r["updated_at"]))
    print(f"{'Code':<6} {'Stage':<22} {'Format':<18} {'Strategist':<16} Name")
    for r in rows:
        star = "⚡" if r.get("is_priority") else " "
        print(f"{r['code']:<6} {STAGE_NAMES.get(r['stage'], r['stage']):<22} {(r['format'] or '—'):<18.18} "
              f"{who.get(r['strategist_id'], '—'):<16.16} {star}{r['name']}")


def cmd_get(args):
    b = find_batch(args.ref)
    hooks = rest("hooks", {"select": "number,name,status,file_link,script_link,duration_seconds",
                           "batch_id": f"eq.{b['id']}", "order": "number.asc.nullslast"})
    assets = rest("batch_assets", {"select": "asset_key,file_name,note,storage_path,created_at",
                                   "batch_id": f"eq.{b['id']}", "order": "created_at.asc"})
    who = names([b["strategist_id"], b["editor_id"]])

    import subprocess
    job = subprocess.run([sys.executable, str(KIT / "scripts" / "new_job.py"), f"{b['code']} {b['name']}",
                          "--editor", who.get(b["editor_id"], ""), "--batch", f"{b['code']} {b['name']}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    job = Path(job)

    def line(label, value):
        if value in (None, "", [], {}):
            return ""
        if isinstance(value, list):
            value = ", ".join(map(str, value))
        return f"- **{label}:** {value}\n"

    brief = (f"# {b['code']} · {b['name']}\n\n"
             f"From the Lumin app ({APP_URL}/batches/{b['id']}), read {time.strftime('%Y-%m-%d %H:%M')}.\n\n"
             + line("Stage", STAGE_NAMES.get(b["stage"], b["stage"])) + line("Priority", "yes" if b["is_priority"] else "")
             + line("Strategist", who.get(b["strategist_id"])) + line("Editor", who.get(b["editor_id"]))
             + line("Format", b["format"]) + line("Angle", b["brief_angle"]) + line("Awareness", b["awareness"])
             + line("Funnel stage", b["funnel_stage"]) + line("Audience", b["audience"])
             + line("Problems", b["problems"]) + line("Concept", b["concept"]) + line("POV", b["pov"])
             + line("Condition", b["condition"]) + line("Headline 1", b["headline_1"])
             + line("Headline 2", b["headline_2"]) + line("Ad details", " / ".join(
                 x for x in [b["ad_details_1"], b["ad_details_2"], b["ad_details_3"]] if x))
             + line("Page details", b["page_details"]) + line("Landing page", b["ad_url"])
             + line("Launch date", b["launch_date"]) + line("Script", b["script_link"])
             + line("Files", b["files_link"]))
    if hooks:
        brief += "\n## Hooks in the app\n\n" + "".join(
            f"- Hook {h['number'] or '?'}: {h['name']} ({h['status'] or 'no status'})"
            + (f", {h['duration_seconds']}s" if h.get("duration_seconds") else "")
            + (f", file: {h['file_link']}" if h.get("file_link") else "") + "\n" for h in hooks)
    if assets:
        brief += "\n## Production files uploaded in the app\n\n" + "".join(
            f"- {a['asset_key']}: {a['file_name']}" + (f" ({a['note']})" if a.get("note") else "") + "\n"
            for a in assets)

    script_note = "no script link on the batch"
    text = ""
    if b["script_link"]:
        text, err = fetch_doc(b["script_link"])
        if text:
            (job / "script.txt").write_text(text, encoding="utf-8")
            script_note = f"script.txt ({len(text):,} characters, from the batch's script tab)"
        else:
            text = ""
            script_note = f"script not downloaded: {err}"
    family = format_family(b["format"], text)
    if family:
        brief += (f"\n## Format family\n\n**{family[1]}** (from {family[3]}). Beat map: `{family[2]}`. "
                  "Plan the ad on these beats.\n")
    else:
        brief += ("\n## Format family\n\nUnknown: no format in the app or the script header. Ask the strategist "
                  "which one it is (see `playbook/formats/README.md`).\n")
    brief += f"\n## Script\n\n{script_note}\n"
    (job / "brief.md").write_text(brief, encoding="utf-8")

    jm = job / "job.md"
    s = jm.read_text(encoding="utf-8")
    if "## Brief\n\n(what the ad is" in s:
        s = s.replace("## Brief\n\n(what the ad is, angle, who's on screen, length, never-show list)",
                      f"## Brief\n\nSee brief.md and script.txt (from batch {b['code']} in the Lumin app).")
        jm.write_text(s, encoding="utf-8")

    print(job)
    print(f"{b['code']} {b['name']} · {STAGE_NAMES.get(b['stage'], b['stage'])} · {b['format'] or 'no format'}"
          f" · strategist {who.get(b['strategist_id'], '?')}")
    print(f"brief.md written · {script_note} · {len(hooks)} hook(s) · {len(assets)} file(s)")
    print(f"format family: {family[1]} -> {family[2]}" if family else "format family: unknown, ask the strategist")
    if not args.no_research:
        try:
            run_research(b, job)
        except (SystemExit, Exception) as failure:  # research must never block getting the batch
            print(f"research skipped: {failure}. Run `python3 scripts/lumin_batch.py research {b['code']}` later.")


def cmd_broll(args):
    words = [w for w in args.words if w.strip()]
    params = {"select": "id,title,scene_type,product,tags,duration_seconds,width,height,notes",
              "kind": "eq.broll", "order": "updated_at.desc", "limit": str(args.limit)}
    ors = []
    for w in words:
        w = re.sub(r"[^\w\s-]", "", w)
        ors.append(f"(title.ilike.*{w}*,notes.ilike.*{w}*,scene_type.ilike.*{w}*,product.ilike.*{w}*,"
                   f"tags.cs.{{{w.lower()}}})")
    if ors:
        params["or"] = ors  # each word must match somewhere (repeated `or` = AND)
    rows = rest("library_items", params)
    if not rows:
        print("Nothing in the B-roll library matches. Try fewer or simpler words.")
        return
    for r in rows:
        dims = f"{r['width']}x{r['height']}" if r.get("width") else ""
        dur = f"{float(r['duration_seconds']):.1f}s" if r.get("duration_seconds") else ""
        tags = ", ".join((r.get("tags") or [])[:6])
        print(f"{r['id']}  {r['title'] or '(untitled)'}  [{', '.join(x for x in [r.get('scene_type'), dur, dims] if x)}]"
              + (f"  tags: {tags}" if tags else ""))


def cmd_broll_get(args):
    rows = rest("library_items", {"select": "id,title,storage_path", "id": f"eq.{args.id}"})
    if not rows or not rows[0].get("storage_path"):
        raise SystemExit("That clip isn't in the library (or has no file).")
    item = rows[0]
    tok, _ = token()
    path = urllib.parse.quote(item["storage_path"])
    signed = http("POST", f"{SUPABASE_URL}/storage/v1/object/sign/{BROLL_BUCKET}/{path}",
                  {"expiresIn": 600}, token=tok)
    url = SUPABASE_URL + "/storage/v1" + signed["signedURL"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    name = f"broll_{slug(item['title'] or item['id'])}{Path(item['storage_path']).suffix}"
    data = urllib.request.urlopen(url, timeout=300).read()
    (out / name).write_bytes(data)
    print(f"{out / name}  ({len(data) / 1e6:.1f} MB)")


# ---------- research ----------
# The app saves the tracked competitors' top video ads from TrendTrack every day (competitor_ads, competitor_ad_days).
# Research reads those days around the batch's date plus our own top ads, downloads the competitors' videos and pulls
# frames, and writes <job>/research/research.md for Claude to read before the plan. No TrendTrack credits are used here.

LIST_SIZES = {"delivery_rank": 12, "running_rank": 6, "copies_rank": 6}
LIST_NAMES = {"delivery_rank": "delivery order", "running_rank": "longest running", "copies_rank": "most copies"}
MAX_VIDEO_BYTES = 120_000_000
HAIR_WORDS = ("hair", "edges", "wig", "wigs", "scalp", "bald", "balding", "thinning", "crown", "follicle", "follicles",
              "shedding", "hairline", "regrow", "regrew", "breakage", "alopecia", "braids", "headband", "batana")
STOP_WORDS = {"batch", "about", "their", "there", "these", "which", "would", "could", "after", "before", "hooks",
              "story", "video", "style", "movie", "pixar", "lumin", "women", "woman"}


def rpc(fn, body):
    tok, _ = token()
    return http("POST", f"{SUPABASE_URL}/rest/v1/rpc/{fn}", body=body, token=tok)


def job_folder(b):
    import subprocess
    who = names([b["editor_id"]])
    out = subprocess.run([sys.executable, str(KIT / "scripts" / "new_job.py"), f"{b['code']} {b['name']}",
                          "--editor", who.get(b["editor_id"], ""), "--batch", f"{b['code']} {b['name']}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(out.splitlines()[-1])


def research_date(b, override):
    today = datetime.date.today()
    if override:
        return datetime.date.fromisoformat(override)
    launch = b.get("launch_date")
    if launch:
        day = datetime.date.fromisoformat(str(launch)[:10])
        return min(day, today)
    return today


def score(row):
    """0-3: how high the ad sat in each of the day's three lists. Winner = in two lists, or long-running with copies."""
    total, lists = 0.0, 0
    for key, size in LIST_SIZES.items():
        rank = row.get(key)
        if rank:
            total += (size + 1 - rank) / size
            lists += 1
    winner = lists >= 2 or ((row.get("days_running") or 0) >= 30 and (row.get("duplicates") or 0) >= 3)
    return round(total, 2), lists, winner


def first_words(text, n=45):
    words = (text or "").split()
    return " ".join(words[:n]) + (" …" if len(words) > n else "")


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return True
    req = urllib.request.Request(url, headers={"User-Agent": "lumin-video-kit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            size = int(r.headers.get("Content-Length") or 0)
            if size > MAX_VIDEO_BYTES:
                return False
            dest.write_bytes(r.read(MAX_VIDEO_BYTES + 1))
        return dest.stat().st_size <= MAX_VIDEO_BYTES
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def run_research(b, job, *, date=None, days=14, top=12, per_brand=2, videos=True, refresh=False):
    out = job / "research"
    md = out / "research.md"
    if md.exists() and not refresh and time.time() - md.stat().st_mtime < 3 * 86400:
        print(f"research: already done {time.strftime('%Y-%m-%d', time.localtime(md.stat().st_mtime))} -> {md} "
              "(--refresh to redo)")
        return md
    out.mkdir(parents=True, exist_ok=True)
    day = research_date(b, date)
    since = day - datetime.timedelta(days=days)

    cols = ("day,ad_id,delivery_rank,running_rank,copies_rank,days_running,duplicates,"
            "competitor_ads(domain,advertiser,first_seen_at,video_url,thumbnail_url,body,transcript,"
            "call_to_action,offer,landing_page,countries),competitors(name)")
    rows = rest("competitor_ad_days", {"select": cols, "day": [f"gte.{since}", f"lte.{day}"],
                                       "order": "day.desc", "limit": "5000"})
    window_note = f"{since} to {day}"
    if not rows:
        latest = rest("competitor_ad_days", {"select": "day", "order": "day.desc", "limit": "1"})
        if latest:
            last = latest[0]["day"]
            rows = rest("competitor_ad_days", {"select": cols, "day": f"eq.{last}", "limit": "5000"})
            window_note = f"no pulls between {since} and {day}; using the nearest pull, {last}"
        else:
            window_note = "no competitor ads saved in the app yet (the daily TrendTrack pull hasn't run)"

    # Each ad's most recent day in the window.
    best = {}
    for r in rows:
        if r["ad_id"] not in best:
            best[r["ad_id"]] = r
    ranked = []
    for r in best.values():
        s, lists, winner = score(r)
        ranked.append({**r, "score": s, "lists": lists, "winner": winner,
                       "brand": (r.get("competitors") or {}).get("name") or (r.get("competitor_ads") or {}).get("domain")})
    # Ads about hair, or about this batch's own words, come first among equals: a lip plumper's winner teaches less.
    topic = set(HAIR_WORDS) | {w for w in re.findall(r"[a-z]{5,}", " ".join(
        str(b.get(k) or "") for k in ("name", "brief_angle", "concept", "problems")).lower()) if w not in STOP_WORDS}
    for r in ranked:
        ad = r.get("competitor_ads") or {}
        words = set(re.findall(r"[a-z]+", f"{ad.get('transcript') or ''} {ad.get('body') or ''}".lower()))
        r["on_topic"] = bool(words & topic)
    ranked.sort(key=lambda r: (r["winner"], r["on_topic"], r["score"], r.get("days_running") or 0), reverse=True)
    # Two groups: proven (running over 30 days) and new and scaling (30 days or less, ranked by copies, i.e.
    # what they're putting money behind right now). Half of the picks each; a group short of ads gives its
    # places to the other.
    def new_key(r):
        return (r["on_topic"], r.get("duplicates") or 0, -(r.get("delivery_rank") or 99))
    fresh = sorted([r for r in ranked if (r.get("days_running") or 999) <= 30], key=new_key, reverse=True)
    proven = [r for r in ranked if (r.get("days_running") or 999) > 30]

    def take(pool, n, group):
        got, per = [], {}
        for r in pool:
            if len(got) >= n:
                break
            if per.get(r["brand"], 0) >= per_brand:
                continue
            got.append({**r, "group": group})
            per[r["brand"]] = per.get(r["brand"], 0) + 1
        return got
    new_picks = take(fresh, top // 2, "new")
    proven_picks = take(proven, top - len(new_picks), "proven")
    if len(proven_picks) < top - len(new_picks):
        new_picks = take(fresh, top - len(proven_picks), "new")
    picked = proven_picks + new_picks

    # Our own top creatives in the 30 days before the date.
    ours = rpc("top_creatives", {"since": str(day - datetime.timedelta(days=30)),
                                 "until": str(day - datetime.timedelta(days=1))}) or []
    ours = [o for o in ours if (o.get("spend") or 0) >= 1000 and (o.get("video_3s_views") or 0) > 0]
    by_spend = sorted(ours, key=lambda o: o["spend"], reverse=True)[:8]
    by_roas = sorted([o for o in ours if o["spend"] >= 2000], key=lambda o: o.get("roas") or 0, reverse=True)[:5]

    # Videos and frames.
    have_ffmpeg = videos and subprocess_ok(["ffprobe", "-version"])
    for r in picked:
        ad = r.get("competitor_ads") or {}
        r["files"] = {}
        if not videos or not ad.get("video_url"):
            continue
        base = f"{slug(r['brand'])}_{r['ad_id'].split('_')[-1]}"
        video = out / "videos" / f"{base}.mp4"
        video.parent.mkdir(exist_ok=True)
        if download(ad["video_url"], video):
            r["files"]["video"] = str(video.relative_to(job))
            if have_ffmpeg:
                frames = out / "frames" / base
                if not frames.exists():
                    subprocess_ok(["bash", str(KIT / "scripts" / "frames.sh"), str(video), str(frames), "6"])
                if frames.exists():
                    r["files"]["frames"] = str(frames.relative_to(job))

    (out / "competitor_ads.json").write_text(json.dumps(picked, indent=1, default=str), encoding="utf-8")

    def money(v):
        return f"${v:,.0f}" if v is not None else "—"

    def pct(v):
        return f"{float(v) * 100:.0f}%" if v is not None else "—"

    lines = [f"# Research for {b['code']} · {b['name']}",
             "",
             f"Made {time.strftime('%Y-%m-%d %H:%M')} for the batch's date {day} "
             f"({'launch date' if b.get('launch_date') and not date else 'today' if not date else 'given'}). "
             f"Format: {b.get('format') or '—'} · angle: {b.get('brief_angle') or '—'} · awareness: {b.get('awareness') or '—'}.",
             "",
             "Claude: read every ad below (transcript, copy, offer, frames), then fill in **Findings** and "
             "**Proposed brief** at the bottom before the plan. See the `research` skill.",
             "",
             "## Our top ads (30 days before the date)",
             ""]
    if by_spend:
        lines += ["| Creative | Spend | ROAS | Hook | Hold |", "|---|---|---|---|---|"]
        lines += [f"| {o.get('label') or o.get('batch_name')} | {money(o['spend'])} | {o.get('roas') or 0:.2f} | "
                  f"{pct(o.get('hook_rate'))} | {pct(o.get('hold_rate'))} |" for o in by_spend]
        if by_roas:
            lines += ["", "Best ROAS with $2k+ spend: " + "; ".join(
                f"{o.get('label') or o.get('batch_name')} ({o.get('roas') or 0:.2f})" for o in by_roas)]
    else:
        lines.append("No video creative with $1k+ spend in that window.")
    lines += ["", f"## Competitors' top ads ({window_note})", "",
              f"{len(best)} ads in the window from {len({r['brand'] for r in ranked})} brands; the {len(picked)} "
              f"picked are below (at most {per_brand} a brand per group). **Proven** = running over 30 days, best first. "
              "**New and scaling** = started in the last 30 days, most copies first: what they're putting money "
              "behind right now. Winner = high in two of the three lists (delivery order, longest running, most "
              "copies), or 30+ days running with 3+ copies. TrendTrack shows no sales.",
              ""]
    headings = {"proven": "### Proven", "new": "### New and scaling"}
    for i, r in enumerate(picked, 1):
        ad = r.get("competitor_ads") or {}
        if headings.get(r["group"]):
            lines += [headings.pop(r["group"]), ""]
        where = ", ".join(f"{LIST_NAMES[k]} #{r[k]}" for k in LIST_SIZES if r.get(k))
        lines += [f"#### {i}. {r['brand']}{' · WINNER' if r['winner'] else ''}{' · on topic' if r['on_topic'] else ''}",
                  f"- {r.get('days_running') or '?'} days running · {r.get('duplicates') or 0} copies · {where} · "
                  f"page: {ad.get('advertiser') or '—'} · seen {r['day']}",
                  f"- Offer: {ad.get('offer') or '—'} · CTA: {ad.get('call_to_action') or '—'} · "
                  f"landing page: {ad.get('landing_page') or '—'}"]
        if r["files"].get("video"):
            lines.append(f"- Video: `{r['files']['video']}`" + (f" · frames: `{r['files']['frames']}/`"
                                                               if r["files"].get("frames") else ""))
        elif ad.get("video_url"):
            lines.append(f"- Video (not downloaded): {ad['video_url']}")
        transcript = (ad.get("transcript") or "").strip()
        lines.append(f"- **Hook:** {first_words(transcript)}" if transcript else
                     "- **No words in TrendTrack's transcript** (music, a song or silent): watch the frames, or "
                     "transcribe the video with `scripts/transcribe.py` if it's sung.")
        if ad.get("body"):
            lines.append(f"- Copy: {first_words(ad['body'], 40)}")
        if transcript:
            lines += ["", "<details><summary>Full transcript</summary>", "", transcript, "", "</details>"]
        lines.append("")
    lines += ["## Findings", "", "(Claude fills this in: what's working for them right now, patterns across brands, "
              "hooks, formats, offers, looks; and what's new compared to our top ads.)", "",
              "## Proposed brief", "", "(Claude fills this in, using the batch's format beat map: 3 hooks adapted to "
              "Lumin, the beats, the look, the offer. The strategist's brief and script win over this.)", ""]
    md.write_text("\n".join(lines), encoding="utf-8")
    vids = sum(1 for r in picked if r["files"].get("video"))
    print(f"research: {len(picked)} competitor ads ({sum(r['winner'] for r in picked)} winners, {vids} videos), "
          f"{len(by_spend)} of our top creatives -> {md}")
    return md


def subprocess_ok(cmd):
    import subprocess
    try:
        return subprocess.run(cmd, capture_output=True, timeout=300).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def cmd_research(args):
    b = find_batch(args.ref)
    job = Path(args.job) if args.job else job_folder(b)
    run_research(b, job, date=args.date, days=args.days, top=args.top, per_brand=args.per_brand,
                 videos=not args.no_videos, refresh=args.refresh)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login").set_defaults(fn=cmd_login)
    sub.add_parser("logout").set_defaults(fn=cmd_logout)
    sub.add_parser("whoami").set_defaults(fn=cmd_whoami)
    p = sub.add_parser("mine"); p.add_argument("--all", action="store_true"); p.set_defaults(fn=cmd_mine)
    p = sub.add_parser("get"); p.add_argument("ref"); p.add_argument("--no-research", action="store_true")
    p.set_defaults(fn=cmd_get)
    p = sub.add_parser("research"); p.add_argument("ref"); p.add_argument("--job", help="job folder (default: the batch's)")
    p.add_argument("--date", help="YYYY-MM-DD to research around (default: launch date, else today)")
    p.add_argument("--days", type=int, default=14, help="days before the date to look at (default 14)")
    p.add_argument("--top", type=int, default=12); p.add_argument("--per-brand", type=int, default=2)
    p.add_argument("--no-videos", action="store_true"); p.add_argument("--refresh", action="store_true")
    p.set_defaults(fn=cmd_research)
    p = sub.add_parser("broll"); p.add_argument("words", nargs="*"); p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_broll)
    p = sub.add_parser("broll-get"); p.add_argument("id"); p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_broll_get)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
