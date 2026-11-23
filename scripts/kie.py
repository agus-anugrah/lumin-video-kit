#!/usr/bin/env python3
"""Kie generation for the kit's AI Commerce route: pictures (nano-banana-pro), clips (Seedance 2.5, Wan 3.0), songs (Suno V6).

Same endpoints the AI Commerce engine uses. Every paid call is written to <job>/kie/ledger.json first and is refused
past the ceiling the editor approved, so a re-run never pays twice. The key comes from KIE_API_KEY (environment only,
never printed or saved).

  python3 scripts/kie.py balance
  python3 scripts/kie.py quote --model seedance --res 480p --seconds 71 --pictures 7 [--songs 1]
  python3 scripts/kie.py approve <job> --reply "<the editor's own words>" --ceiling 18.20
  python3 scripts/kie.py picture <job> --id hero_wig --prompt "..." [--ref path ...] [--out <file>]
  python3 scripts/kie.py clip <job> --id s03 --seconds 12 --prompt "..." --ref <still or sheet> ... [--model seedance|wan] [--res 480p|720p] [--audio]
  python3 scripts/kie.py song <job> --lyrics lyrics.txt --style "..." --title "..." --seconds 120
  python3 scripts/kie.py fetch <job>          # download anything that finished (after a timeout or a dropped connection)
  python3 scripts/kie.py spent <job>
"""
import argparse, hashlib, json, mimetypes, os, sys, time, urllib.parse, urllib.request, uuid

KIE = "https://api.kie.ai/api/v1"
KIE_UPLOAD = "https://kieai.redpandaai.co/api/file-stream-upload"
CREDITS_PER_USD = 200          # observed Nov 2026: a 12 s Seedance 480p clip = 336 credits = $1.68
MODELS = {
    "seedance": {"id": "bytedance/seedance-2-5", "tag": "@image", "audio": "generate_audio", "min": 4, "max": 15,
                 "res": {"480p": "480p", "720p": "720p", "1080p": "1080p"}, "usd_per_s": {"480p": 0.14, "720p": 0.315}},
    "wan": {"id": "wan/3-0-video", "tag": "Image ", "audio": "audio", "min": 2, "max": 15,
            "res": {"480p": "480P", "720p": "720P", "1080p": "1080P"}, "usd_per_s": {"480p": 0.04}},
}
PICTURE = {"id": "nano-banana-pro", "usd": 0.09}      # 18 credits each, observed
SONG = {"id": "ai-music-api/generate", "usd": 0.06}   # Suno V6, 12 credits per call (two versions), observed


# ---------------------------------------------------------------- plumbing
def key():
    k = os.environ.get("KIE_API_KEY")
    if not k: sys.exit("KIE_API_KEY is not set. Add it to your shell profile (never paste it into chat), then open a new terminal.")
    return k


def http(url, method="GET", body=None, headers=None, raw=False, timeout=120):
    h = dict(headers or {}); data = None
    if isinstance(body, (dict, list)): data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    elif isinstance(body, bytes): data = body
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=timeout) as r:
        b = r.read()
    return b if raw else json.loads(b)


class Ledger:
    def __init__(self, job):
        self.dir = os.path.join(job, "kie"); os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "ledger.json")
        self.s = json.load(open(self.path)) if os.path.exists(self.path) else {"approved": None, "spend": [], "uploads": {}, "jobs": {}}

    def save(self):
        json.dump(self.s, open(self.path + ".part", "w"), indent=2); os.replace(self.path + ".part", self.path)

    def spent(self): return round(sum(x["usd"] for x in self.s["spend"]), 2)


def balance():
    return http(f"{KIE}/chat/credit", headers={"Authorization": f"Bearer {key()}"}).get("data")


def upload(L, path):
    ck = f"{os.path.abspath(path)}:{os.path.getsize(path)}:{int(os.path.getmtime(path))}"
    hit = L.s["uploads"].get(ck)
    if hit and time.time() - hit["t"] < 20 * 3600: return hit["url"]       # Kie keeps uploads about 24 h
    bnd = uuid.uuid4().hex; name = f"{uuid.uuid4().hex[:8]}-{os.path.basename(path)}"
    parts = [f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in {"uploadPath": "lumin-kit", "fileName": name}.items()]
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\nContent-Type: {ctype}\r\n\r\n".encode() + open(path, "rb").read() + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    r = http(KIE_UPLOAD, "POST", b"".join(parts), {"Authorization": f"Bearer {key()}", "Content-Type": f"multipart/form-data; boundary={bnd}"})
    url = (r.get("data") or {}).get("downloadUrl") or (r.get("data") or {}).get("fileUrl")
    if not url: raise RuntimeError(f"Kie upload refused ({r.get('code')}): {r.get('msg')}")
    L.s["uploads"][ck] = {"url": url, "t": time.time()}; L.save(); return url


def job_id(kind, name, payload):
    """A changed prompt or reference is a new job; the same one is never submitted twice."""
    return f"{kind} {name} " + hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:8]


def create(L, jid, model, inp, usd):
    job = L.s["jobs"].setdefault(jid, {})
    if job.get("task"): return job["task"]
    if not L.s["approved"]: sys.exit(f"Not approved: nothing was sent. Quote the cost, get the editor's go, then: kie.py approve <job> --reply \"<their words>\" --ceiling <usd>")
    if L.spent() + usd > L.s["approved"]["ceiling_usd"] + 0.001:
        sys.exit(f"{jid}: not sent. The approved ceiling ${L.s['approved']['ceiling_usd']:.2f} would be passed (spent ${L.spent():.2f}). Ask the editor before raising it.")
    for i in range(7):
        r = http(f"{KIE}/jobs/createTask", "POST", {"model": model, "input": inp}, {"Authorization": f"Bearer {key()}"})
        tid = (r.get("data") or {}).get("taskId")
        if r.get("code") == 200 and tid:
            job.update({"task": tid, "model": model, "submitted": time.strftime("%Y-%m-%d %H:%M:%S")})
            L.s["spend"].append({"what": jid, "usd": usd, "task": tid, "at": job["submitted"]}); L.save()
            return tid
        if str(r.get("code")) == "402": sys.exit("Kie says the balance is too low (402). Nothing was charged. Top up, then run the same command again.")
        if str(r.get("code")) != "429": raise RuntimeError(f"Kie refused {jid} ({r.get('code')}): {r.get('msg')}")
        time.sleep(min(30, 2 ** (i + 1)))
    raise RuntimeError(f"{jid}: Kie's rate limit refused it every time. Nothing was created or charged.")


def wait(task, timeout_s=2700, every=8):
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            d = http(f"{KIE}/jobs/recordInfo?taskId={urllib.parse.quote(task)}", headers={"Authorization": f"Bearer {key()}"}, timeout=60).get("data") or {}
        except Exception:
            time.sleep(every); continue
        st = str(d.get("state") or d.get("status") or "").lower()
        if st in ("success", "complete", "completed"):
            urls = json.loads(d.get("resultJson") or "{}").get("resultUrls") or []
            if not urls:                                        # Suno answers in response.data[].audio_url
                resp = d.get("response") or {}
                if isinstance(resp, str): resp = json.loads(resp or "{}")
                urls = [x.get("audio_url") or x.get("audioUrl") for x in (resp.get("data") or resp.get("sunoData") or []) if x.get("audio_url") or x.get("audioUrl")]
            if not urls: raise RuntimeError("Kie finished without a file")
            return urls
        if st in ("fail", "failed", "error"): raise RuntimeError("Kie job failed: " + str(d.get("failMsg") or d.get("failCode") or "no reason given"))
        time.sleep(every)
    raise TimeoutError(f"task {task} is still running. Run `kie.py fetch <job>` later; it is not paid for twice.")


def fetch_url(url, out, tries=5):
    for i in range(tries):
        try:
            data = http(url, raw=True, timeout=600)
            open(out + ".part", "wb").write(data); os.replace(out + ".part", out); return out
        except Exception:
            if i == tries - 1: raise
            time.sleep(4 * (i + 1))


def finish(L, jid, outs):
    job = L.s["jobs"][jid]; urls = wait(job["task"])
    saved = []
    for u, o in zip(urls, outs):
        os.makedirs(os.path.dirname(o) or ".", exist_ok=True); fetch_url(u, o); saved.append(o)
    job["files"] = saved; job["done"] = time.strftime("%Y-%m-%d %H:%M:%S"); L.save()
    for o in saved: print("saved", o)
    return saved


# ---------------------------------------------------------------- commands
def cmd_quote(a):
    m = MODELS[a.model]; rate = m["usd_per_s"].get(a.res)
    if rate is None: sys.exit(f"No price recorded for {a.model} at {a.res}. Recorded: {m['usd_per_s']}")
    v = a.seconds * rate; p = a.pictures * PICTURE["usd"]; s = a.songs * SONG["usd"]
    first = v + p + s; cap = first + v * 0.75
    print(f"{a.model} {a.res}: {a.seconds:g} s = ${v:.2f} · {a.pictures} pictures = ${p:.2f} · {a.songs} songs = ${s:.2f}")
    print(f"first pass about ${first:.2f} · ceiling with re-render room ${cap:.2f} · about {round(first * CREDITS_PER_USD)} credits")
    try: print(f"Kie balance now: {balance()} credits (about ${balance() / CREDITS_PER_USD:.2f})")
    except SystemExit: raise
    except Exception as e: print("balance not read:", e)


def cmd_approve(a):
    if len(a.reply.strip()) < 2: sys.exit("--reply needs the editor's own words")
    L = Ledger(a.job); L.s["approved"] = {"reply": a.reply, "ceiling_usd": a.ceiling, "at": time.strftime("%Y-%m-%d %H:%M:%S")}; L.save()
    print(f"approved up to ${a.ceiling:.2f} for {a.job} ({a.reply!r})")


def cmd_picture(a):
    L = Ledger(a.job); refs = a.ref or []
    inp = {"prompt": a.prompt, "aspect_ratio": a.aspect, "resolution": "1K", "output_format": "jpg"}
    jid = job_id("picture", a.id, {**inp, "refs": refs})
    inp["image_input"] = [upload(L, r) for r in refs]
    create(L, jid, PICTURE["id"], inp, PICTURE["usd"]); print("submitted", jid)
    finish(L, jid, [a.out or os.path.join(a.job, "stills", a.id + ".jpg")])


def cmd_clip(a):
    m = MODELS[a.model]; L = Ledger(a.job); refs = a.ref or []
    secs = int(max(m["min"], min(m["max"], round(a.seconds))))
    rate = m["usd_per_s"].get(a.res)
    if rate is None: sys.exit(f"No price recorded for {a.model} at {a.res}")
    prompt = a.prompt
    if refs and m["tag"] == "@image": prompt = "REFERENCES: " + " ".join(f"@image{i + 1} = {os.path.basename(r)}." for i, r in enumerate(refs)) + " " + prompt
    inp = {"prompt": prompt, "duration": secs, "resolution": m["res"][a.res], "aspect_ratio": a.aspect, m["audio"]: bool(a.audio)}
    jid = job_id("clip", a.id, {**inp, "refs": refs, "model": a.model})
    inp["reference_image_urls"] = [upload(L, r) for r in refs]
    create(L, jid, m["id"], inp, secs * rate); print("submitted", jid)
    finish(L, jid, [a.out or os.path.join(a.job, "clips", a.id + ".mp4")])


def cmd_song(a):
    L = Ledger(a.job); lyrics = open(a.lyrics).read().strip()
    inp = {"custom_mode": True, "instrumental": False, "model": "V6", "title": a.title[:80], "lyrics": lyrics, "style": a.style[:1000],
           "vocal_gender": a.vocal, "duration": int(a.seconds)}
    if a.negative: inp["negative_tags"] = a.negative
    jid = job_id("song", a.title, inp)
    create(L, jid, SONG["id"], inp, SONG["usd"]); print("submitted", jid)
    finish(L, jid, [os.path.join(a.job, "music", f"song_{i + 1}.mp3") for i in range(2)])


def cmd_fetch(a):
    L = Ledger(a.job)
    for jid, job in L.s["jobs"].items():
        if job.get("task") and not job.get("done"):
            kind, name = jid.split(" ")[:2]
            sub = {"picture": ("stills", ".jpg"), "clip": ("clips", ".mp4"), "song": ("music", ".mp3")}[kind]
            outs = [os.path.join(a.job, sub[0], f"{name}{sub[1]}")] if kind != "song" else [os.path.join(a.job, "music", f"song_{i + 1}.mp3") for i in range(2)]
            try: finish(L, jid, outs)
            except Exception as e: print(jid, "-", e)


def cmd_spent(a):
    L = Ledger(a.job); ap = L.s["approved"] or {}
    print(f"spent about ${L.spent():.2f} of ${ap.get('ceiling_usd', 0):.2f} approved ({len(L.s['spend'])} paid calls)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("balance").set_defaults(fn=lambda a: print(f"{balance()} credits"))
    q = sub.add_parser("quote"); q.add_argument("--model", choices=MODELS, default="seedance"); q.add_argument("--res", default="480p")
    q.add_argument("--seconds", type=float, required=True); q.add_argument("--pictures", type=int, default=0); q.add_argument("--songs", type=int, default=0); q.set_defaults(fn=cmd_quote)
    ap = sub.add_parser("approve"); ap.add_argument("job"); ap.add_argument("--reply", required=True); ap.add_argument("--ceiling", type=float, required=True); ap.set_defaults(fn=cmd_approve)
    pi = sub.add_parser("picture"); pi.add_argument("job"); pi.add_argument("--id", required=True); pi.add_argument("--prompt", required=True)
    pi.add_argument("--ref", nargs="*"); pi.add_argument("--aspect", default="9:16"); pi.add_argument("--out"); pi.set_defaults(fn=cmd_picture)
    cl = sub.add_parser("clip"); cl.add_argument("job"); cl.add_argument("--id", required=True); cl.add_argument("--seconds", type=float, required=True)
    cl.add_argument("--prompt", required=True); cl.add_argument("--ref", nargs="*"); cl.add_argument("--model", choices=MODELS, default="seedance")
    cl.add_argument("--res", default="480p"); cl.add_argument("--aspect", default="9:16"); cl.add_argument("--audio", action="store_true"); cl.add_argument("--out"); cl.set_defaults(fn=cmd_clip)
    so = sub.add_parser("song"); so.add_argument("job"); so.add_argument("--lyrics", required=True); so.add_argument("--style", required=True)
    so.add_argument("--title", required=True); so.add_argument("--seconds", type=float, required=True); so.add_argument("--vocal", default="f")
    so.add_argument("--negative", default="male vocals, rap, EDM drop"); so.set_defaults(fn=cmd_song)
    fe = sub.add_parser("fetch"); fe.add_argument("job"); fe.set_defaults(fn=cmd_fetch)
    sp = sub.add_parser("spent"); sp.add_argument("job"); sp.set_defaults(fn=cmd_spent)
    a = p.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
