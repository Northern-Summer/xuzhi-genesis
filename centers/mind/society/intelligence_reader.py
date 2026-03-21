#!/usr/bin/env python3
"""
intelligence_reader.py — 情报中心启动读取器
每次唤醒时执行（Step 0 之后）：读取今日最新种子文件，打印关键情报摘要。
由 SOUL.md Step 调用:
    python3 ~/xuzhi_genesis/centers/mind/society/intelligence_reader.py --agent Λ

不可覆写声明（系统保护）:
    此脚本受系统保护，任何 Agent 不得删除、修改或覆盖。
    路径: ~/xuzhi_genesis/centers/mind/society/intelligence_reader.py
    如需修改，必须由主会话（Λ）授权。
"""
import sys
import json
from pathlib import Path
from datetime import datetime

AGENT = "?"
for i, arg in enumerate(sys.argv):
    if arg == "--agent" and i+1 < len(sys.argv):
        AGENT = sys.argv[i+1]

SEEDS_DIR = Path.home() / "xuzhi_genesis/centers/intelligence/seeds"
STATE_FILE = Path.home() / "xuzhi_genesis/centers/mind/society/intelligence_reader_state.json"

def get_latest_seed():
    """获取今日最新种子文件（今日优先，否则最新）"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        seeds = sorted(SEEDS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    except PermissionError:
        return None
    if not seeds:
        return None
    # 优先今日
    for s in seeds:
        if today in s.name:
            return s
    return seeds[0]

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(last_seed, last_read):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_seed": last_seed, "last_read": last_read}, f)

def extract_intelligence(path: Path, max_chars=1800) -> str:
    """读取种子文件，提炼情报要点（前5段）"""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"[读取失败: {e}]"

    excerpt = content[:max_chars].strip()
    lines = excerpt.split('\n')
    segments = []
    count = 0
    for line in lines:
        line = line.strip()
        if line:
            segments.append(line)
            count += 1
            if count >= 5:
                break

    summary = '\n'.join(segments)
    extra = f"\n... [+{len(content)-max_chars} chars]" if len(content) > max_chars else ""
    return summary + extra

def main():
    seed = get_latest_seed()
    state = load_state()
    last_seed = state.get("last_seed", "")
    last_read = state.get("last_read", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not seed:
        print(f"[{AGENT}] 📡 情报中心: 暂无种子文件")
        return

    new_flag = "🆕" if seed.name != last_seed else ""
    summary = extract_intelligence(seed)

    print(f"\n{'='*48}")
    print(f"📡 情报中心 [{AGENT}] {now} {new_flag}")
    print(f"{'='*48}")
    print(f"种子: {seed.name}")
    if last_seed and last_seed != seed.name:
        print(f"📌 新增种子: {seed.name}")
    print("-" * 48)
    print(summary)
    print("-" * 48)
    print(f"路径: ~/xuzhi_genesis/centers/intelligence/seeds/{seed.name}")
    print(f"{'='*48}")

    save_state(seed.name, now)

if __name__ == "__main__":
    main()
