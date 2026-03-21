#!/usr/bin/env python3
"""
log_feedback.py — 记录任务反馈到日志
用法:
    python3 log_feedback.py --agent Λ --task "描述" --feedback positive --reason "原因" [--lesson "教训"]
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

LOG_FILE = Path.home() / "xuzhi_genesis/centers/mind/society/feedback_log.jsonl"

def append_log(entry: dict):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="记录任务反馈")
    parser.add_argument("--agent", required=True, help="Agent代码，如 Λ")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--feedback", required=True, choices=["positive", "negative", "neutral"], help="反馈类型")
    parser.add_argument("--reason", default="", help="原因")
    parser.add_argument("--lesson", default="", help="提炼的教训")
    args = parser.parse_args()

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": args.agent,
        "task": args.task,
        "feedback": args.feedback,
        "reason": args.reason,
        "lesson": args.lesson,
    }
    append_log(entry)
    print(f"✅ 反馈已记录: [{args.agent}] {args.feedback} — {args.task}")

if __name__ == "__main__":
    main()
