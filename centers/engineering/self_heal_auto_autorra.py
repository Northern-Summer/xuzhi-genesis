#!/usr/bin/env python3
"""
AutoRA Research Cycle Job Auto-Healer
Xuzhi-Lambda-Ergo (Λ) — Engineering Center
Auto-heals: sessionTarget=main + agentTurn, missing jobs, delivery errors
"""
import json
import os
import subprocess
import sys

def get_autorra_job():
    return {
        "name": "AutoRA Research Cycle",
        "schedule": {"kind": "cron", "expr": "0 0,6,12,18 * * *", "tz": "Asia/Shanghai"},
        "payload": {
            "kind": "agentTurn",
            "message": (
                "You are the AutoRA Researcher (Θ). Run: "
                "cd ~/xuzhi_genesis/centers/engineering/harness && "
                "python3 scripts/autorun.py 2>&1 | tail -20. "
                "If tests failed, fix them: cd ~/xuzhi_genesis/centers/engineering/harness && "
                "python3 -m pytest tests/ -q --tb=short. "
                "Commit any fixes with: cd ~/xuzhi_genesis && "
                "git add -A && git commit -m \"Θ: AutoRA cycle fix\" && git push origin master. "
                "Report output."
            )
        },
        "delivery": {"mode": "announce", "channel": "webchat"},
        "sessionTarget": "isolated",
        "enabled": True
    }

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def load_jobs():
    path = os.path.expanduser("~/.openclaw/cron/jobs.json")
    with open(path) as f:
        return json.load(f), path

def save_jobs(jobs, path):
    with open(path, "w") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    f"{path} written"

def fix():
    jobs, path = load_jobs()
    # Remove all AutoRA-related jobs (bad configs)
    original_count = len(jobs)
    jobs = [j for j in jobs if "autorra" not in j.get("name","").lower() 
            and "research cycle" not in j.get("name","").lower()]
    removed = original_count - len(jobs)
    # Add correct job
    jobs.append(get_autorra_job())
    save_jobs(jobs, path)
    print(f"[Λ] AutoRA: removed {removed} bad config(s), added correct job")
    return True

if __name__ == "__main__":
    ok = fix()
    sys.exit(0 if ok else 1)
