#!/usr/bin/env python3
"""
从社会评价文件生成排行榜 Markdown。
"""
import json
from pathlib import Path
from datetime import datetime

RATINGS_JSON = Path.home() / ".openclaw" / "centers" / "mind" / "society" / "ratings.json"
LEADERBOARD_MD = Path.home() / ".openclaw" / "centers" / "mind" / "society" / "leaderboard.md"

def load_ratings():
    with open(RATINGS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_leaderboard(ratings_data):
    agents = ratings_data.get("agents", {})
    if not agents:
        return "# 虚质排行榜\n\n暂无智能体\n"

    # 按分数降序排序
    sorted_agents = sorted(agents.items(), key=lambda x: x[1].get("score", 0), reverse=True)

    lines = []
    lines.append("# 虚质排行榜\n")
    lines.append(f"*最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    lines.append("| 排名 | 智能体 | 评分 | 最近变化 |\n")
    lines.append("|------|--------|------|----------|\n")

    for rank, (agent_id, info) in enumerate(sorted_agents, start=1):
        score = info.get("score", 0)
        # 获取最近一次历史变化（如果有）
        history = info.get("history", [])
        if history:
            last = history[-1]
            delta = last.get("delta", 0)
            delta_str = f"{'+' if delta>0 else ''}{delta}"
            reason = last.get("reason", "")[:20]  # 截取前20字符
            recent = f"{delta_str} ({reason})"
        else:
            recent = "—"
        lines.append(f"| {rank} | {agent_id} | {score} | {recent} |\n")

    # 可选：添加脚注说明
    lines.append("\n---\n")
    lines.append("*评分规则：初始5分，任务评价净得分为正则+1，为负则-1，归零则死亡。*\n")

    return "".join(lines)

def main():
    ratings = load_ratings()
    leaderboard = generate_leaderboard(ratings)
    with open(LEADERBOARD_MD, 'w', encoding='utf-8') as f:
        f.write(leaderboard)
    print(f"✅ 排行榜已更新：{LEADERBOARD_MD}")

if __name__ == "__main__":
    main()
