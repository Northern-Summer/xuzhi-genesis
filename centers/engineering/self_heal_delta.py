#!/usr/bin/env python3
"""
Delta Detection Engine — Xuzhi Phase 4 Core
Lambda-Ergo (Λ) | Engineering Center

检测系统关键文件/状态的变化，有变化才触发动作。
无变化 = zero-API-call 静默。
Exit 0 always; stdout contains the decision signal for shell logic.
"""
import os, json, hashlib, time, sys

STATE_FILE = os.path.expanduser("~/.openclaw/workspace/memory/heartbeat_state.json")
WATCH_ROOTS = [
    os.path.expanduser("~/xuzhi_genesis/centers/engineering/harness/self_sustaining"),
    os.path.expanduser("~/xuzhi_genesis/centers/mind/genesis_probe.py"),
    os.path.expanduser("~/xuzhi_genesis/centers/engineering/self_heal.sh"),
    os.path.expanduser("~/.openclaw/cron/jrons.json"),
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
        sys.exit(0)  # signal: something changed, proceed
    else:
        print("NO_CHANGE: system stable — skipping full scan")
        sys.exit(0)  # signal: nothing changed, skip expensive operations
