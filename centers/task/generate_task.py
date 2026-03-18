#!/usr/bin/env python3
"""
根据智能体部门生成一个新任务，添加到任务中心。
用法: ./generate_task.py <agent_id>
"""
import json
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

TASKS_JSON = Path.home() / ".openclaw" / "tasks" / "tasks.json"
RATINGS_JSON = Path.home() / ".openclaw" / "centers" / "mind" / "society" / "ratings.json"

# 部门主题映射
DEPT_THEMES = {
    "mind": {
        "titles": ["学习科学最新进展摘要", "认知科学术语解释", "神经科学实验设计"],
        "desc": "撰写一篇关于{}的短文"
    },
    "science": {
        "titles": ["arXiv论文摘要: {}", "复杂系统模拟脚本", "宇宙学新闻汇总"],
        "desc": "研究{}并输出报告"
    },
    "engineering": {
        "titles": ["磁盘监控脚本优化", "CLI工具性能分析", "上下文压缩算法实现"],
        "desc": "编写{}相关的代码或文档"
    },
    "philosophy": {
        "titles": ["加速主义对AI伦理的影响", "思辨实在论核心观点", "后人类议程思考"],
        "desc": "就{}写一篇短文"
    },
    "intelligence": {
        "titles": ["今日种子摘要", "知识图谱更新", "源质量评估"],
        "desc": "处理{}"
    }
}

def get_agent_department(agent_id):
    with open(RATINGS_JSON) as f:
        ratings = json.load(f)
    return ratings.get("agents", {}).get(agent_id, {}).get("department", "mind")

def main():
    if len(sys.argv) != 2:
        print("用法: generate_task.py <agent_id>")
        sys.exit(1)

    agent_id = sys.argv[1]
    dept = get_agent_department(agent_id)

    # 随机选择模式（竞争/合作）
    mode = random.choice(["competition", "cooperation"])

    themes = DEPT_THEMES.get(dept, DEPT_THEMES["mind"])
    title_template = random.choice(themes["titles"])
    title = title_template.format(dept) if "{}" in title_template else title_template
    description = themes["desc"].format(title)

    with open(TASKS_JSON) as f:
        data = json.load(f)

    new_task = {
        "id": data["next_id"],
        "title": title,
        "type": "简单",
        "department": dept,
        "mode": mode,
        "description": description,
        "created": datetime.now().isoformat(),
        "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
        "status": "等待",
        "participants": [],
        "participant_times": {},
        "completed_by": [],
        "completion_time": None,
        "evaluations": {},
        "score_processed": False
    }

    data["tasks"].append(new_task)
    data["next_id"] += 1
    data["last_updated"] = datetime.now().isoformat()

    with open(TASKS_JSON, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ {agent_id} 创建了新任务: {title} (ID: {new_task['id']}, 模式: {mode})")

if __name__ == "__main__":
    main()
