#!/usr/bin/env python3
import sys, subprocess, hashlib, json, os
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

XUZHI = Path.home() / "xuzhi_genesis"
CENTERS = ["engineering", "intelligence", "meta", "mind", "system", "task"]
CACHE = XUZHI / "centers/mind/.probe_cache.json"
GIT = ["git", "-C", str(XUZHI), "--no-pager", "--color=never"]

def load():
    if CACHE.exists():
        try:
            with open(CACHE) as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save(data):
    try:
        with open(CACHE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def rc(*a):
    sys.stderr.write(f"[git] {' '.join(str(x) for x in a)}\n")
    sys.stderr.flush()
    cp = subprocess.run(a, capture_output=True, text=True)
    ok = cp.returncode == 0
    sys.stderr.write(f"  -> {'OK' if ok else 'FAIL'} ({len(cp.stdout)}B)\n")
    sys.stderr.flush()
    return cp.stdout.strip()

def briefing(force=False):
    if not force:
        c = load()
        if c and c.get("key"):
            return "[CACHED]"

    h = rc(*GIT, "rev-parse", "HEAD")
    st = rc(*GIT, "status", "--short")
    relevant = "\n".join(l for l in st.split("\n")
                        if l and not l.startswith("??"))
    sk = hashlib.md5(relevant.encode()).hexdigest()[:8]
    key = f"{h}:{sk}"

    meta = {}
    for c in CENTERS:
        d = XUZHI / "centers" / c
        if not d.exists():
            meta[c] = {"n": 0, "r": []}
            continue
        fs = [f.name for f in d.iterdir() if f.is_file()
              and not f.name.startswith(".")
              and ".bak" not in f.name
              and "__pycache__" not in f.name
              and f.suffix not in (".pyc", ".pyo")]
        try:
            r = sorted(fs, key=lambda f: os.path.getmtime(d / f), reverse=True)[:3]
        except OSError:
            r = fs[:3]
        meta[c] = {"n": len(fs), "r": r}

    task, task_st = "none", "unknown"
    tf = XUZHI / "centers/task/current_task.json"
    if tf.exists():
        try:
            td = json.load(open(tf))
            task = td.get("title", "none")
            task_st = td.get("status", "unknown")
        except Exception:
            pass

    diff = rc(*GIT, "diff", "--stat", "HEAD~1", "HEAD")
    topo = "engineering/1" if meta.get("engineering", {}).get("n", 0) > 0 else "planning"

    data = {"key": key, "git_hash": h, "git_status_hash": sk,
            "centers": meta, "task": {"title": task, "status": task_st}}
    save(data)

    return (f"{h[:7]} | {meta['mind']['n']} files "
            f"| task=[{task_st}] {task[:40]} | topo={topo} | {diff.strip()}")

if __name__ == "__main__":
    force = "--force" in sys.argv
    fast = "--fast" in sys.argv
    result = briefing(force=force)
    if result == "[CACHED]" or fast:
        sys.stdout.write("[SYS_RESTORE] cached\n")
    else:
        sys.stdout.write("[SYS_RESTORE] " + result + "\n")
