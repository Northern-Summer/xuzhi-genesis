#!/usr/bin/env python3
"""
Delta Detection Engine — Xuzhi Phase 4 Core
Xi (Ξ) | Engineering Center

检测系统关键文件/状态的变化，有变化才触发动作。
Exit 0 always; stdout contains the decision signal.
"""
import os, json, hashlib, time, sys

STATE_FILE = os.path.expanduser("~/.openclaw/workspace/memory/heartbeat_state.json")
# Watch targets — changes here trigger full self_heal scan
WATCH_ROOTS = [
    os.path.expanduser("~/xuzhi_genesis/centers/engineering/harness/self_sustaining"),
    os.path.expanduser("~/xuzhi_genesis/centers/mind/genesis_probe.py"),
    os.path.expanduser("~/xuzhi_genesis/centers/engineering/self_heal.sh"),
    os.path.expanduser("~/.openclaw/cron/jobs.json"),
    os.path.expanduser("~/xuzhi_genesis/centers/engineering/self_heal_auto_autorra.py"),
    os.path.expanduser("~/xuzhi_genesis/centers/engineering/parse_crons.py"),
]

def hash_file(path):
    if not os.path.exists(path):
        return "MISSING"
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:12]

def snapshot():
    return {"ts": time.time(), "files": {path: hash_file(path) for path in WATCH_ROOTS}}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return None

def save_state(state):
    # Save atomically to a temp file first, then rename (avoids partial writes)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.rename(tmp, STATE_FILE)

def detect():
    prev = load_state()
    curr = snapshot()
    if prev is None:
        return True, {"reason": "first_run", "changed": list(WATCH_ROOTS)}, curr

    changed = []
    for path in WATCH_ROOTS:
        h = hash_file(path)
        if path not in prev.get("files", {}) or prev["files"][path] != h:
            changed.append({"path": path, "old": prev["files"].get(path, "?"), "new": h})

    return bool(changed), {"changed": changed, "files": curr["files"]}, curr

if __name__ == "__main__":
    changed, detail, curr = detect()
    if changed:
        print(f"CHANGED: {len(detail['changed'])} file(s)")
        for c in detail["changed"]:
            print(f"  {os.path.basename(c['path'])}: {c['old']} → {c['new']}")
        save_state(curr)
        sys.exit(0)
    else:
        print("NO_CHANGE: system stable — skipping full scan")
        sys.exit(0)
