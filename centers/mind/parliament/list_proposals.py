#!/usr/bin/env python3
"""
列出所有提案。
用法: list_proposals.py [--status pending|voting|passed|rejected]
"""
import json
import argparse
from pathlib import Path

PROPOSALS_FILE = Path(__file__).parent / "proposals.json"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", help="按状态过滤")
    args = parser.parse_args()

    with open(PROPOSALS_FILE) as f:
        data = json.load(f)

    proposals = data["proposals"]
    if args.status:
        proposals = [p for p in proposals if p["status"] == args.status]

    print("提案列表：")
    for p in proposals:
        status = p["status"]
        deadline = p["voting_deadline"][:16] if p["voting_deadline"] else "未开始"
        votes = len(p["votes"])
        print(f"  #{p['id']} [{status}] {p['title']} (投票截止 {deadline}, 已投票 {votes} 票)")

if __name__ == "__main__":
    main()
