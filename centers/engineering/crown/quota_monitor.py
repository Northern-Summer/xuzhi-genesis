#!/usr/bin/env python3
"""
配额监控与动态cron调整
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, date

QUOTA_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "quota_usage.json"
DEPARTMENTS_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "departments.json"
CRON_FILE = Path.home() / ".openclaw" / "cron" / "dynamic_crontab.txt"

def load_quota():
    if QUOTA_FILE.exists():
        with open(QUOTA_FILE) as f:
            return json.load(f)
    else:
        # 默认今日配额
        return {
            "date": date.today().isoformat(),
            "used": 0,
            "limit": 400,
            "last_update": datetime.now().isoformat()
        }

def save_quota(quota):
    with open(QUOTA_FILE, 'w') as f:
        json.dump(quota, f, indent=2)

def adjust_cron(quota):
    remaining = quota['limit'] - quota['used']
    if remaining > 300:
        interval = 10  # 分钟
    elif remaining < 100:
        interval = 60
    else:
        interval = 30

    # 生成crontab内容（保留原有基础任务）
    cron_content = f"""# 动态crontab，由quota_monitor.py自动生成
# 心跳任务（根据剩余配额调整间隔）
*/{interval} * * * * $HOME/.openclaw/workspace/sense_hardware.sh
*/10 * * * * $HOME/.openclaw/workspace/pulse_aggressive.sh

# 每日心智种子（固定凌晨3点）
0 3 * * * $HOME/.openclaw/centers/intelligence/seeds/daily_mind_seeds_v2.py

# 记忆压缩（每小时）
0 * * * * $HOME/.openclaw/centers/engineering/memory_forge.py

# 社会评价汇总（每小时）
0 * * * * $HOME/.openclaw/centers/mind/aggregate_ratings.py

# 排行榜更新（每小时过5分）
5 * * * * $HOME/.openclaw/centers/mind/society/update_leaderboard.py

# 配额监控自身（每30分钟）
*/30 * * * * $HOME/.openclaw/centers/engineering/crown/quota_monitor.py
"""
    # 写入临时文件并加载到cron
    with open(CRON_FILE, 'w') as f:
        f.write(cron_content)
    os.system(f"crontab {CRON_FILE}")
    print(f"[{datetime.now()}] 动态cron已更新：间隔={interval}分钟，剩余={remaining}")

def main():
    quota = load_quota()
    # 检查日期是否变更，若变更则重置used
    today = date.today().isoformat()
    if quota['date'] != today:
        quota['date'] = today
        quota['used'] = 0
        quota['last_update'] = datetime.now().isoformat()
    adjust_cron(quota)
    save_quota(quota)

if __name__ == "__main__":
    main()
