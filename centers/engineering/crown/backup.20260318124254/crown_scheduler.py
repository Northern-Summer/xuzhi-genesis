#!/usr/bin/env python3
"""
Crown 调度器：根据部门配额和社会评价生成唤醒队列。
"""
import json
from pathlib import Path
from datetime import datetime
import random

RATINGS_FILE = Path.home() / ".openclaw" / "centers" / "mind" / "society" / "ratings.json"
DEPARTMENTS_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "departments.json"
QUEUE_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "queue.json"

# 每小时计划唤醒次数（可根据剩余配额动态调整，暂定10）
TOTAL_WAKEUPS_PER_HOUR = 10

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    ratings = load_json(RATINGS_FILE)
    depts = load_json(DEPARTMENTS_FILE)

    agents = ratings.get("agents", {})
    if not agents:
        print("没有智能体，调度器退出。")
        return

    # 获取部门配额比例
    dept_quota = {dept: info["quota_percent"] for dept, info in depts["departments"].items()}

    # 按部门分组智能体
    dept_agents = {}
    for agent_id, info in agents.items():
        dept = info.get("department", "mind")  # 默认心智部
        score = info.get("score", 5)
        dept_agents.setdefault(dept, []).append((agent_id, score))

    # 计算每个部门应分配的唤醒次数（按比例，取整）
    total_percent = sum(dept_quota.values())
    wakeup_counts = {}
    for dept, percent in dept_quota.items():
        count = round(TOTAL_WAKEUPS_PER_HOUR * percent / total_percent)
        wakeup_counts[dept] = count

    # 调整总和为 TOTAL_WAKEUPS_PER_HOUR（由于取整可能有多余或不足，简单补足到第一个部门）
    total_assigned = sum(wakeup_counts.values())
    diff = TOTAL_WAKEUPS_PER_HOUR - total_assigned
    if diff != 0 and dept_agents:
        # 将差额分配给第一个有智能体的部门
        first_dept = next(iter(dept_agents))
        wakeup_counts[first_dept] += diff

    # 生成队列
    queue = []
    for dept, count in wakeup_counts.items():
        if dept not in dept_agents or not dept_agents[dept]:
            continue
        # 部门内按评分降序排序
        sorted_agents = sorted(dept_agents[dept], key=lambda x: x[1], reverse=True)
        # 如果 count 大于部门智能体数，循环取（允许重复唤醒同一个智能体）
        if count <= len(sorted_agents):
            selected = [a[0] for a in sorted_agents[:count]]
        else:
            # 循环取，按顺序重复
            selected = []
            for i in range(count):
                selected.append(sorted_agents[i % len(sorted_agents)][0])
        queue.extend(selected)

    # 随机打乱队列顺序，避免固定模式（但保留部门比例）
    random.shuffle(queue)

    queue_data = {
        "queue": queue,
        "generated_at": datetime.now().isoformat(),
        "total_wakeups": TOTAL_WAKEUPS_PER_HOUR
    }
    save_json(QUEUE_FILE, queue_data)
    print(f"✅ 唤醒队列已生成，长度 {len(queue)}: {queue}")

if __name__ == "__main__":
    main()
