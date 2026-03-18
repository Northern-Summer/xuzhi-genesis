#!/usr/bin/env python3
"""
处理提案状态转换与计票，并关联任务中心。
应定期运行（例如每15分钟）。
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

PROPOSALS_FILE = Path(__file__).parent / "proposals.json"
TASKS_FILE = Path.home() / ".openclaw" / "tasks" / "tasks.json"
AGENTS_DIR = Path.home() / ".openclaw" / "agents"
DEPARTMENTS_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "departments.json"

def total_agents():
    return len([d for d in AGENTS_DIR.iterdir() if d.is_dir()])

def create_task_for_proposal(proposal):
    """在任务中心创建一个关联任务"""
    if not TASKS_FILE.exists():
        print("任务文件不存在，无法创建关联任务")
        return
    with open(TASKS_FILE) as f:
        tasks_data = json.load(f)
    # 检查是否已存在关联任务（避免重复）
    for t in tasks_data["tasks"]:
        if t.get("related_proposal_id") == proposal["id"]:
            return
    new_task = {
        "id": tasks_data["next_id"],
        "title": f"议会投票: {proposal['title']}",
        "type": "议会",
        "department": "mind",
        "description": f"提案描述: {proposal['description']}\n截止日期: {proposal['voting_deadline']}",
        "created": datetime.now().isoformat(),
        "deadline": proposal["voting_deadline"][:10],  # 只取日期部分
        "status": "进行",
        "participants": [],
        "completed_by": [],
        "evaluations": {},
        "related_proposal_id": proposal["id"],
        "score_processed": False
    }
    tasks_data["tasks"].append(new_task)
    tasks_data["next_id"] += 1
    tasks_data["last_updated"] = datetime.now().isoformat()
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks_data, f, indent=2)
    print(f"已为提案 #{proposal['id']} 创建关联任务 #{new_task['id']}")

def complete_task_for_proposal(proposal, result):
    """将关联任务标记为完成"""
    if not TASKS_FILE.exists():
        return
    with open(TASKS_FILE) as f:
        tasks_data = json.load(f)
    for t in tasks_data["tasks"]:
        if t.get("related_proposal_id") == proposal["id"]:
            t["status"] = "完成"
            t["completion_time"] = datetime.now().isoformat()
            t["completion_note"] = f"提案结果: {result}"
            break
    tasks_data["last_updated"] = datetime.now().isoformat()
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks_data, f, indent=2)
    print(f"已更新关联任务状态为完成，结果: {result}")

def handle_passed_proposal(proposal):
    """调用外部处理脚本执行通过后的操作"""
    handler = Path(__file__).parent / "handle_passed_proposal.py"
    if handler.exists():
        subprocess.run([str(handler), str(proposal["id"])])
    else:
        print("未找到处理脚本 handle_passed_proposal.py，请手动处理提案")

def main():
    with open(PROPOSALS_FILE) as f:
        data = json.load(f)

    now = datetime.now()
    changed = False

    # 1. 将 pending 提案转为 voting（每次只激活一个）
    active_voting = any(p["status"] == "voting" for p in data["proposals"])
    if not active_voting:
        for p in data["proposals"]:
            if p["status"] == "pending":
                p["status"] = "voting"
                p["voting_deadline"] = (now + timedelta(days=3)).isoformat()
                print(f"提案 #{p['id']} 进入投票阶段，截止 {p['voting_deadline']}")
                # 在任务中心创建关联任务
                create_task_for_proposal(p)
                changed = True
                break

    # 2. 检查超时的投票提案
    total = total_agents()
    for p in data["proposals"]:
        if p["status"] != "voting":
            continue
        deadline = datetime.fromisoformat(p["voting_deadline"])
        if now < deadline:
            continue

        # 统计票数
        votes = p["votes"]
        yes = sum(1 for v in votes.values() if v == "yes")
        no = sum(1 for v in votes.values() if v == "no")
        # 弃权不计入

        # 规则：赞成票 ≥ 总智能体数 * 2/3 且 赞成 > 反对
        required = (total * 2) / 3
        if yes >= required and yes > no:
            p["status"] = "passed"
            p["result"] = "passed"
            print(f"提案 #{p['id']} 通过（赞成 {yes}/{total}，反对 {no}）")
            # 调用通过处理脚本
            handle_passed_proposal(p)
        else:
            p["status"] = "rejected"
            p["result"] = "rejected"
            print(f"提案 #{p['id']} 未通过（赞成 {yes}/{total}，反对 {no}）")
        # 更新关联任务
        complete_task_for_proposal(p, p["result"])
        changed = True

    if changed:
        with open(PROPOSALS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
