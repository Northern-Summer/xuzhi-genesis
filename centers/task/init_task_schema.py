#!/usr/bin/env python3
"""
初始化任务中心数据结构，确保 tasks.json 包含评价所需字段。
"""
import json
import os
from pathlib import Path

TASKS_JSON = Path.home() / ".openclaw" / "tasks" / "tasks.json"

def init_schema():
    if not TASKS_JSON.exists():
        # 创建默认结构
        default = {
            "tasks": [],
            "next_id": 1,
            "last_updated": "2026-03-17T12:00:00Z"
        }
        TASKS_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_JSON, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        print("✅ 已创建 tasks.json")
        return

    # 读取现有文件
    with open(TASKS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    modified = False
    for task in data.get("tasks", []):
        # 为每个任务添加评价相关字段（如果缺失）
        if "completed_by" not in task:
            task["completed_by"] = None
            modified = True
        if "completion_time" not in task:
            task["completion_time"] = None
            modified = True
        if "evaluations" not in task:
            task["evaluations"] = {}
            modified = True
        if "score_processed" not in task:
            task["score_processed"] = False
            modified = True

    if modified:
        with open(TASKS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("✅ 已更新 tasks.json，添加评价字段")
    else:
        print("✅ tasks.json 已包含所需字段，无需修改")

if __name__ == "__main__":
    init_schema()
