#!/usr/bin/env python3
"""
迁移任务数据格式：增加 mode 字段，将 completed_by 转为列表。
"""
import json
from pathlib import Path

TASKS_JSON = Path.home() / ".openclaw" / "tasks" / "tasks.json"

def migrate():
    if not TASKS_JSON.exists():
        print("任务文件不存在，跳过。")
        return

    with open(TASKS_JSON) as f:
        data = json.load(f)

    modified = False
    for task in data.get("tasks", []):
        # 添加 mode 字段（默认 competition）
        if "mode" not in task:
            task["mode"] = "competition"
            modified = True
        # 将 completed_by 转为列表
        if "completed_by" in task and not isinstance(task["completed_by"], list):
            old = task["completed_by"]
            task["completed_by"] = [old] if old else []
            modified = True
        # 确保 participants 存在
        if "participants" not in task:
            task["participants"] = []
            modified = True

    if modified:
        with open(TASKS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        print("任务数据格式已迁移。")
    else:
        print("无需迁移。")

if __name__ == "__main__":
    migrate()
