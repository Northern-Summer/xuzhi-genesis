#!/usr/bin/env python3
"""
投票脚本：对已完成任务进行好/不好评价。
用法: ./vote_on_task.py <task_id> <agent_id> <good|bad>
"""
import json
import sys
from pathlib import Path
from datetime import datetime

TASKS_JSON = Path.home() / ".openclaw" / "tasks" / "tasks.json"

def main():
    if len(sys.argv) != 4:
        print("用法: vote_on_task.py <task_id> <agent_id> <good|bad>")
        sys.exit(1)

    task_id = sys.argv[1]
    agent_id = sys.argv[2]
    vote = sys.argv[3].lower()

    if vote not in ("good", "bad"):
        print("❌ 评价必须是 'good' 或 'bad'")
        sys.exit(1)

    # 加载任务
    with open(TASKS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 查找任务
    task = None
    for t in data["tasks"]:
        if str(t["id"]) == task_id:
            task = t
            break

    if not task:
        print(f"❌ 未找到任务 ID {task_id}")
        sys.exit(1)

    # 检查任务是否已完成
    if not task.get("completed_by"):
        print(f"❌ 任务 {task_id} 尚未完成，不能评价")
        sys.exit(1)

    # 检查是否已过期（可选，但逾期自动标记为不好已在外部处理）
    # 这里只记录评价

    # 初始化 evaluations 字典（如果不存在）
    if "evaluations" not in task:
        task["evaluations"] = {}

    # 记录评价（覆盖之前的评价）
    task["evaluations"][agent_id] = vote
    task["last_updated"] = datetime.now().isoformat()

    # 保存
    with open(TASKS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已记录 {agent_id} 对任务 {task_id} 的评价: {vote}")

if __name__ == "__main__":
    main()
