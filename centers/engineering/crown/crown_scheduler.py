#!/usr/bin/env python3
"""
Crown 调度器增强版：根据剩余配额和部门配额生成唤醒队列。
"""
import json
from pathlib import Path
from datetime import datetime
import random

RATINGS_FILE = Path.home() / ".openclaw" / "centers" / "mind" / "society" / "ratings.json"
DEPARTMENTS_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "departments.json"
QUOTA_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "quota_usage.json"
QUEUE_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "queue.json"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    ratings = load_json(RATINGS_FILE)
    depts = load_json(DEPARTMENTS_FILE)
    quota = load_json(QUOTA_FILE)

    remaining = quota['limit'] - quota['used']
    if remaining > 300:
        wakeups_per_hour = 15
    elif remaining > 200:
        wakeups_per_hour = 10
    elif remaining > 100:
        wakeups_per_hour = 6
    elif remaining > 50:
        wakeups_per_hour = 3
    else:
        wakeups_per_hour = 1

    agents = ratings.get("agents", {})
    if not agents:
        print("没有智能体，调度器退出。")
        return

    dept_quota = {dept: info["quota_percent"] for dept, info in depts["departments"].items()}

    dept_agents = {}
    for agent_id, info in agents.items():
        dept = info.get("department", "mind")
        score = info.get("score", 5)
        dept_agents.setdefault(dept, []).append((agent_id, score))

    total_percent = sum(dept_quota.values())
    wakeup_counts = {}
    for dept, percent in dept_quota.items():
        count = round(wakeups_per_hour * percent / total_percent)
        wakeup_counts[dept] = max(count, 1)

    total_assigned = sum(wakeup_counts.values())
    diff = wakeups_per_hour - total_assigned
    if diff != 0 and dept_agents:
        first_dept = next(iter(dept_agents))
        wakeup_counts[first_dept] += diff

    queue = []
    for dept, count in wakeup_counts.items():
        if dept not in dept_agents or not dept_agents[dept]:
            continue
        sorted_agents = sorted(dept_agents[dept], key=lambda x: x[1], reverse=True)
        if count <= len(sorted_agents):
            selected = [a[0] for a in sorted_agents[:count]]
        else:
            selected = []
            for i in range(count):
                selected.append(sorted_agents[i % len(sorted_agents)][0])
        queue.extend(selected)

    random.shuffle(queue)

    queue_data = {
        "queue": queue,
        "generated_at": datetime.now().isoformat(),
        "total_wakeups": wakeups_per_hour,
        "remaining_quota": remaining
    }
    save_json(QUEUE_FILE, queue_data)
    print(f"✅ 唤醒队列已生成，剩余配额 {remaining}，每小时唤醒 {wakeups_per_hour} 次")

if __name__ == "__main__":
    main()
