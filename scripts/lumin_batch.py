#!/usr/bin/env python3
"""Read your batches from the Lumin app (read-only), with your own app login.

  python3 scripts/lumin_batch.py login                 # once, in your own terminal (asks for your password)
  python3 scripts/lumin_batch.py whoami
  python3 scripts/lumin_batch.py mine [--all]          # your open batches (--all: every stage)
  python3 scripts/lumin_batch.py get 3946              # batch by code (or part of its name): brief, hooks,
                                                       # script, files -> a job folder; prints its path
  python3 scripts/lumin_batch.py broll church wig      # search the app's B-roll library
  python3 scripts/lumin_batch.py broll-get <id> --out jobs/<job>/source   # download one clip

You only ever see what you can see in the app (the app's own access rules apply). Nothing is changed in
the app. Your password is never stored or shown: the login keeps a session token in
~/.lumin-kit/session.json (only your user can read it). `logout` deletes it.
"""
import argparse
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login").set_defaults(fn=cmd_login)
    sub.add_parser("logout").set_defaults(fn=cmd_logout)
    sub.add_parser("whoami").set_defaults(fn=cmd_whoami)
    p = sub.add_parser("mine"); p.add_argument("--all", action="store_true"); p.set_defaults(fn=cmd_mine)
    p = sub.add_parser("get"); p.add_argument("ref"); p.set_defaults(fn=cmd_get)
    p = sub.add_parser("broll"); p.add_argument("words", nargs="*"); p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_broll)
    p = sub.add_parser("broll-get"); p.add_argument("id"); p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_broll_get)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
