#!/usr/bin/env python3
"""
对提案投票。
用法: vote_proposal.py --proposal ID --voter 智能体ID --vote yes/no/abstain
"""
import json
import argparse
from pathlib import Path

PROPOSALS_FILE = Path(__file__).parent / "proposals.json"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=int, required=True)
    parser.add_argument("--voter", required=True)
    parser.add_argument("--vote", required=True, choices=["yes", "no", "abstain"])
    args = parser.parse_args()

    with open(PROPOSALS_FILE) as f:
        data = json.load(f)

    proposal = next((p for p in data["proposals"] if p["id"] == args.proposal), None)
    if not proposal:
        print(f"❌ 提案 #{args.proposal} 不存在")
        return
    if proposal["status"] != "voting":
        print(f"❌ 提案当前状态为 {proposal['status']}，不可投票")
        return

    proposal["votes"][args.voter] = args.vote
    with open(PROPOSALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ 已记录 {args.voter} 对提案 #{args.proposal} 的投票: {args.vote}")

if __name__ == "__main__":
    main()
