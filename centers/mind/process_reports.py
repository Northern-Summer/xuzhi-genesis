#!/usr/bin/env python3
"""
处理举报：统计投票，执行奖惩。应定期运行（例如每15分钟）。
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

XUZHI_HOME = Path.home() / 'xuzhi_genesis'
REPORTS_FILE = XUZHI_HOME / 'centers' / 'mind' / 'society' / 'reports.json'
RATINGS_FILE = XUZHI_HOME / 'centers' / 'mind' / 'society' / 'ratings.json'
AGENTS_DIR = Path.home() / '.openclaw' / 'agents'

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def update_agent_score(ratings, agent, delta, reason):
    if agent not in ratings['agents']:
        return
    old = ratings['agents'][agent]['score']
    new = old + delta
    ratings['agents'][agent]['score'] = new
    ratings['agents'][agent]['history'].append({
        'date': datetime.now().isoformat(),
        'delta': delta,
        'reason': reason
    })
    print(f"更新 {agent}: {old} -> {new} ({reason})")

def main():
    reports = load_json(REPORTS_FILE)
    ratings = load_json(RATINGS_FILE) if RATINGS_FILE.exists() else None
    changed = False

    for report in reports['reports']:
        if report['status'] != 'pending':
            continue
        # 假设投票窗口为 3 个周期（这里简化：检查是否超过 1 小时）
        created = datetime.fromisoformat(report['created_at'])
        if datetime.now() - created < timedelta(hours=1):
            continue  # 投票未结束

        votes = report['votes']
        total_agents = len([d for d in AGENTS_DIR.iterdir() if d.is_dir()])
        # 如果投票数少于总智能体数的 1/3，视为未达成共识，暂不处理
        if len(votes) < total_agents // 3:
            report['status'] = 'insufficient_votes'
            print(f"举报 {report['id']} 投票不足，标记为未处理")
            continue

        yes = sum(1 for v in votes.values() if v == 'yes')
        no = sum(1 for v in votes.values() if v == 'no')
        # 若赞成票 ≥ 2/3 总智能体数，则作弊成立
        if yes >= (2 * total_agents / 3):
            # 惩罚作弊者
            if ratings:
                update_agent_score(ratings, report['accused'], -2, f"作弊成立 (举报 {report['id']})")
                # 奖励举报者
                update_agent_score(ratings, report['reporter'], 1, f"举报成功 (举报 {report['id']})")
            report['result'] = 'guilty'
            report['executed'] = True
            print(f"举报 {report['id']} 成立，已执行惩罚")
        else:
            # 若反对票 ≥ 2/3，则举报者恶意
            if no >= (2 * total_agents / 3):
                if ratings:
                    update_agent_score(ratings, report['reporter'], -1, f"恶意举报 (举报 {report['id']})")
                report['result'] = 'malicious'
                report['executed'] = True
                print(f"举报 {report['id']} 被认定为恶意，举报者扣分")
            else:
                # 无明确多数，标记为争议
                report['status'] = 'disputed'
                print(f"举报 {report['id']} 无明确结论，暂不处理")
                continue
        report['status'] = 'decided'
        changed = True

    if changed:
        save_json(REPORTS_FILE, reports)
        if ratings:
            save_json(RATINGS_FILE, ratings)
        # 广播结果
        broadcast = Path.home() / '.openclaw' / 'workspace' / 'broadcast.md'
        with open(broadcast, 'a') as f:
            f.write("\n[心智中心] 举报处理完成。\n")

if __name__ == '__main__':
    main()
