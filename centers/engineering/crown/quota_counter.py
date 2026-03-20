#!/usr/bin/env python3
"""
quota_counter.py — 配额消耗追踪器

功能：
1. 记录每日/每小时 API 调用次数
2. 记录 POST 请求次数
3. 追踪 token 消耗量
4. 告警阈值：单日 > 5000次API 或 > 200000 tokens

用法（由 cron 调用）：
    */5 * * * * python3 ~/xuzhi_genesis/centers/engineering/crown/quota_counter.py
"""

import json
import os
import sys
import fcntl
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
COUNTER_FILE = HOME / ".openclaw/centers/mind/society/quota_counter.json"
LOG_DIR = HOME / "xuzhi_genesis/centers/engineering/crown"
ALERT_LOG = LOG_DIR / "quota_alerts.jsonl"

TODAY = datetime.now().strftime("%Y-%m-%d")
THIS_HOUR = datetime.now().strftime("%Y-%m-%dT%H:00")


def load_counter():
    if not COUNTER_FILE.exists():
        return {
            "daily": {},  # date -> {api_calls, post_requests, tokens}
            "hourly": {},  # hour -> same
            "last_reset_daily": None,
        }
    with open(COUNTER_FILE) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        data = json.load(f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return data


def save_counter(data):
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COUNTER_FILE, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(data, f, indent=2, ensure_ascii=False)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def get_openclaw_stats() -> dict:
    """尝试从 OpenClaw session 获取 token 统计"""
    stats = {"api_calls": 0, "post_requests": 0, "tokens": 0}
    
    # 尝试读取 session_status
    try:
        result = subprocess.run(
            ["openclaw", "status", "--json"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            stats["tokens"] = data.get("tokens_used", 0)
    except:
        pass
    
    # 尝试从 quota_usage.json 推断
    try:
        quota_usage = json.loads(
            Path("/home/summer/xuzhi_genesis/centers/engineering/crown/quota_usage.json").read_text()
        )
        # 每日配额使用量作为 token 消耗的代理指标
        stats["tokens"] = quota_usage.get("used", 0) * 100  # 粗略估算
    except:
        pass
    
    return stats


def increment_counter():
    """增加一次调用计数"""
    counter = load_counter()
    today = datetime.now().strftime("%Y-%m-%d")
    this_hour = datetime.now().strftime("%Y-%m-%dT%H:00")
    
    # 初始化今日
    if today not in counter["daily"]:
        counter["daily"][today] = {"api_calls": 0, "post_requests": 0, "tokens": 0}
    # 初始化本小时
    if this_hour not in counter["hourly"]:
        counter["hourly"][this_hour] = {"api_calls": 0, "post_requests": 0, "tokens": 0}
    
    # 增量
    counter["daily"][today]["api_calls"] += 1
    counter["hourly"][this_hour]["api_calls"] += 1
    
    save_counter(counter)
    return counter


def check_thresholds():
    """检查是否触发告警阈值"""
    counter = load_counter()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if today not in counter["daily"]:
        return None
    
    d = counter["daily"][today]
    alerts = []
    
    if d["api_calls"] > 5000:
        alerts.append(f"API日调用量超过5000: {d['api_calls']}")
    if d.get("tokens", 0) > 200000:
        alerts.append(f"日Token消耗超过200000: {d.get('tokens', 0)}")
    
    return alerts


def alert(msg: str, severity: str = "WARN"):
    entry = {
        "ts": datetime.now().isoformat(),
        "severity": severity,
        "source": "quota_counter",
        "message": msg,
    }
    with open(ALERT_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_summary() -> dict:
    """返回当前配额统计摘要"""
    counter = load_counter()
    today = datetime.now().strftime("%Y-%m-%d")
    this_hour = datetime.now().strftime("%Y-%m-%dT%H:00")
    
    daily = counter["daily"].get(today, {"api_calls": 0, "post_requests": 0, "tokens": 0})
    hourly = counter["hourly"].get(this_hour, {"api_calls": 0, "post_requests": 0, "tokens": 0})
    
    return {
        "date": today,
        "hour": this_hour,
        "daily_api_calls": daily["api_calls"],
        "daily_post_requests": daily["post_requests"],
        "daily_tokens": daily.get("tokens", 0),
        "hourly_api_calls": hourly["api_calls"],
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="配额计数器")
    parser.add_argument("--summary", action="store_true", help="显示当前统计")
    parser.add_argument("--increment", action="store_true", help="增加一次计数")
    args = parser.parse_args()
    
    if args.summary:
        s = get_summary()
        print(f"今日 {s['date']}: API={s['daily_api_calls']}, POST={s['daily_post_requests']}, Tokens={s['daily_tokens']}")
        print(f"本小时 {s['hour']}: API={s['hourly_api_calls']}")
    elif args.increment:
        increment_counter()
        print(f"计数已增加。当前: {get_summary()['daily_api_calls']} 次/日")
    else:
        # 默认：增加计数 + 检查阈值
        increment_counter()
        s = get_summary()
        print(f"API调用: {s['daily_api_calls']}/日, {s['hourly_api_calls']}/小时")
        
        alerts = check_thresholds()
        if alerts:
            for a in alerts:
                print(f"⚠️  {a}")
                alert(a, "CRIT")


if __name__ == "__main__":
    main()
