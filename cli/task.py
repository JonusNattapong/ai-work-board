#!/usr/bin/env python3
"""ai-work-board CLI — Markdown tasks + tiny CLI."""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "work-items"
APP = ROOT / "app"
STATUSES = ["queued", "running", "review", "done"]
FIELDS = ["id", "title", "status", "agent", "type", "prio", "progress", "created", "updated"]


def today() -> str:
    return datetime.date.today().isoformat()


def now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def slugify(text: str) -> str:
    s = re.sub(r"[^0-9A-Za-z\u0E00-\u0E7F]+", "-", text).strip("-").lower()
    return s[:48] or "task"


def status_dir(status: str) -> Path:
    d = ITEMS / status
    d.mkdir(parents=True, exist_ok=True)
    return d


def all_files() -> list[Path]:
    out = []
    for st in STATUSES:
        d = ITEMS / st
        if d.is_dir():
            out.extend(sorted(d.glob("*.md")))
    return out


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}
    logs: list[str] = []
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            head = text[3:end]
            body = text[end + 4 :]
            for line in head.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            if "## Log" in body:
                pre, logpart = body.split("## Log", 1)
                logs = [l for l in logpart.splitlines() if l.strip().startswith("-")]
                body = pre
            meta["_body"] = body.strip()
    meta["_logs"] = logs
    meta["_path"] = path
    meta["_status"] = path.parent.name
    return meta


def render(meta: dict) -> str:
    lines = ["---"]
    for f in FIELDS:
        lines.append(f"{f}: {meta.get(f, '')}")
    lines.append("---")
    lines.append("")
    body = meta.get("_body", "").strip()
    if body:
        lines.append(body)
        lines.append("")
    lines.append("## Log")
    lines.append("")
    logs = meta.get("_logs", [])
    if logs:
        lines.extend(logs)
    else:
        lines.append(f"- {now()} สร้างงาน")
    return "\n".join(lines).rstrip() + "\n"


def save(meta: dict) -> None:
    meta["updated"] = today()
    meta["_path"].write_text(render(meta), encoding="utf-8")


def find(tid: str) -> dict:
    for f in all_files():
        m = parse(f)
        if str(m.get("id")) == str(tid):
            return m
    die(f"ไม่พบงาน id={tid}")


def move(meta: dict, status: str) -> None:
    old = meta["_path"]
    target = status_dir(status) / old.name
    new_meta = meta
    new_meta["status"] = status
    meta["_path"] = target
    save(new_meta)
    if old.resolve() != target.resolve():
        old.unlink()


def add_log(meta: dict, text: str) -> None:
    logs = meta.get("_logs") or []
    logs.append(f"- {now()} {text}")
    meta["_logs"] = logs


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------- commands ----------

def cmd_ls(args) -> None:
    rows = [parse(f) for f in all_files()]
    if args.status:
        rows = [r for r in rows if r["_status"] == args.status]
    if not rows:
        print("ยังไม่มีงานในบอร์ด")
        return
    print(f"{'ID':<5} {'STATUS':<8} {'PROG':<5} {'PRI':<7} {'AGENT':<10} TITLE")
    for r in rows:
        print(
            f"{r.get('id',''):<5} {r['_status']:<8} {r.get('progress',0):<5} "
            f"{r.get('prio',''):<7} {r.get('agent',''):<10} {r.get('title','')}"
        )


def cmd_add(args) -> None:
    ids = []
    for f in all_files():
        v = parse(f).get("id")
        if v and str(v).isdigit():
            ids.append(int(v))
    tid = max(ids, default=0) + 1
    name = f"{tid:04d}-{slugify(args.title)}.md"
    path = status_dir("queued") / name
    meta = {
        "id": tid,
        "title": args.title,
        "status": "queued",
        "agent": args.agent,
        "type": args.type,
        "prio": args.prio,
        "progress": 0,
        "created": today(),
        "updated": today(),
        "_body": args.desc or "",
        "_logs": [],
        "_path": path,
    }
    save(meta)
    add_log(meta, f"สร้างงาน ({args.agent}/{args.prio})")
    save(meta)
    print(f"เพิ่มงาน id={tid} -> {path.relative_to(ROOT)}")


def cmd_start(args) -> None:
    meta = find(args.id)
    if meta["_status"] == "running":
        print(f"id={args.id} อยู่ running อยู่แล้ว")
        return
    move(meta, "running")
    add_log(meta, "เริ่มงาน")
    save(meta)
    print(f"id={args.id} -> running")


def cmd_log(args) -> None:
    meta = find(args.id)
    add_log(meta, args.message)
    save(meta)
    print(f"บันทึก log ของ id={args.id} แล้ว")


def cmd_progress(args) -> None:
    v = max(0, min(100, args.value))
    if v % 10 != 0:
        die("progress ต้องเป็นขั้น 10 (เช่น 10, 20, 30 ...)")
    meta = find(args.id)
    meta["progress"] = v
    add_log(meta, f"progress {v}%")
    save(meta)
    print(f"id={args.id} progress={v}%")


def _set_status(args, status: str) -> None:
    meta = find(args.id)
    if meta["_status"] == "done" and status != "done":
        die("งานที่ done แล้วห้ามย้อนกลับ")
    if status == "done":
        meta["progress"] = 100
    move(meta, status)
    add_log(meta, f"ย้ายไป {status}")
    save(meta)
    print(f"id={args.id} -> {status}")


def cmd_review(args) -> None:
    _set_status(args, "review")


def cmd_done(args) -> None:
    _set_status(args, "done")


def cmd_serve(args) -> None:
    import http.server
    import socketserver

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(APP), **kw)

        def do_GET(self):
            if self.path.startswith("/api/tasks"):
                from urllib.parse import urlparse

                if urlparse(self.path).path == "/api/tasks.json":
                    import json

                    tasks = []
                    for f in all_files():
                        m = parse(f)
                        t = m["_path"].read_text(encoding="utf-8")
                        logpart = t.split("## Log", 1)[1] if "## Log" in t else ""
                        tasks.append(
                            {
                                "id": m.get("id"),
                                "title": m.get("title", ""),
                                "status": m["_status"],
                                "agent": m.get("agent", ""),
                                "type": m.get("type", ""),
                                "prio": m.get("prio", ""),
                                "progress": int(m.get("progress", 0) or 0),
                                "updated": m.get("updated", ""),
                                "log": [l.strip("- ").strip() for l in logpart.splitlines() if l.strip().startswith("-")],
                            }
                        )
                        tasks.sort(key=lambda x: int(x["id"]))
                    body = json.dumps(tasks, ensure_ascii=False, indent=2)
                    data = body.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            return super().do_GET()

        def log_message(self, *a):
            pass

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as httpd:
        print(f"board: http://localhost:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(prog="task.py", description="ai-work-board CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ls", help="list tasks")
    p.add_argument("--status", choices=STATUSES)
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser("add", help="create task")
    p.add_argument("title")
    p.add_argument("--agent", default="unassigned")
    p.add_argument("--type", default="task", choices=["agent", "task", "bug", "chore"])
    p.add_argument("--prio", default="normal", choices=["low", "normal", "high", "urgent"])
    p.add_argument("--desc", default="")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("start", help="move to running")
    p.add_argument("id")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("log", help="append log entry")
    p.add_argument("id")
    p.add_argument("message")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("progress", help="set progress in steps of 10")
    p.add_argument("id")
    p.add_argument("value", type=int)
    p.set_defaults(func=cmd_progress)

    p = sub.add_parser("review", help="move to review")
    p.add_argument("id")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("done", help="move to done")
    p.add_argument("id")
    p.set_defaults(func=cmd_done)

    p = sub.add_parser("serve", help="serve the HTML board")
    p.add_argument("--port", type=int, default=8777)
    p.set_defaults(func=cmd_serve)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
