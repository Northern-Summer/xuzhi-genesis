#!/usr/bin/env python3
"""
标记任务为完成。
- 合作模式：任何参与者完成，所有参与者都视为完成者（模型信息仅记录完成者）。
- 竞争模式：只允许一个完成者（调用者），其他参与者视为未完成。
用法: ./complete_task.py <task_id> <agent_id> [--model MODEL] [--calls CALLS]
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

TASKS_JSON = Path.home() / ".openclaw" / "tasks" / "tasks.json"

def main():
    parser = argparse.ArgumentParser(description='完成任务')
    parser.add_argument('task_id', type=int, help='任务ID')
    parser.add_argument('agent_id', help='完成任务的智能体ID')
    parser.add_argument('--model', help='完成任务使用的主要模型名称')
    parser.add_argument('--calls', type=int, default=1, help='模型调用次数')
    args = parser.parse_args()

    # 加载任务数据
    try:
        with open(TASKS_JSON) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 任务文件不存在: {TASKS_JSON}")
        sys.exit(1)

    # 查找任务
    task = None
    for t in data["tasks"]:
        if t["id"] == args.task_id:
            task = t
            break

    if not task:
        print(f"❌ 未找到任务 {args.task_id}")
        sys.exit(1)

    # 检查任务状态
    if task.get("status") not in ("进行", "竞争"):
        print(f"❌ 任务 {args.task_id} 状态不是'进行'，当前: {task.get('status')}")
        sys.exit(1)

    participants = task.get("participants", [])
    if args.agent_id not in participants:
        print(f"❌ {args.agent_id} 不是任务 {args.task_id} 的参与者")
        sys.exit(1)

    mode = task.get("mode", "competition")  # 默认竞争

    if mode == "cooperation":
        # 合作模式：所有参与者都视为完成者
        task["completed_by"] = participants[:]
        task["status"] = "完成"
        print(f"✅ 合作任务 {args.task_id} 已完成，所有参与者共同完成: {participants}")
    else:  # competition
        # 竞争模式：只有调用者完成
        task["completed_by"] = [args.agent_id]
        task["status"] = "完成"
        print(f"✅ 竞争任务 {args.task_id} 已完成，完成者: {args.agent_id}")

    # 记录模型信息（如果提供了）
    if args.model:
        if "participant_models" not in task:
            task["participant_models"] = {}
        task["participant_models"][args.agent_id] = {
            "primary_model": args.model,
            "calls": args.calls,
            "all_models": [args.model]
        }

    task["completion_time"] = datetime.now().isoformat()
    task["last_updated"] = datetime.now().isoformat()

    # 保存
    with open(TASKS_JSON, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
