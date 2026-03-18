#!/usr/bin/env python3
"""
发起提案。
用法: propose.py --title "标题" --desc "描述" --proposer 智能体ID
"""
import json
import argparse
from pathlib import Path
from datetime import datetime

PROPOSALS_FILE = Path(__file__).parent / "proposals.json"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--desc", required=True)
    parser.add_argument("--proposer", required=True)
    args = parser.parse_args()

    with open(PROPOSALS_FILE) as f:
        data = json.load(f)

    new_id = data["last_id"] + 1
    proposal = {
        "id": new_id,
        "title": args.title,
        "description": args.desc,
        "proposer": args.proposer,
        "created_at": datetime.now().isoformat(),
        "voting_deadline": None,
        "status": "pending",
        "votes": {},
        "result": None,
        "executed": False
    }
    data["proposals"].append(proposal)
    data["last_id"] = new_id

    with open(PROPOSALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ 提案 #{new_id} 已创建，等待进入投票阶段。")

if __name__ == "__main__":
    main()
