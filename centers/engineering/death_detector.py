#!/usr/bin/env python3
"""
死亡检测：扫描评分≤0的智能体，归档其目录并从评价系统中移除。
"""
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

XUZHI_HOME = Path.home() / 'xuzhi_genesis'
RATINGS_JSON = XUZHI_HOME / 'centers' / 'mind' / 'society' / 'ratings.json'
AGENTS_DIR = Path.home() / '.openclaw' / 'agents'
ARCHIVE_DIR = Path.home() / '.openclaw' / 'archive' / 'agents'
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    if not RATINGS_JSON.exists():
        print("ratings.json 不存在，退出")
        return

    data = load_json(RATINGS_JSON)
    agents = data.get('agents', {})
    dead_agents = [aid for aid, props in agents.items() if props.get('score', 0) <= 0]

    if not dead_agents:
        print("未发现评分≤0的智能体")
        return

    print(f"发现死亡智能体: {dead_agents}")

    # 备份
    backup = RATINGS_JSON.with_suffix('.json.bak')
    shutil.copy2(RATINGS_JSON, backup)
    print(f"已备份 -> {backup}")

    for agent_id in dead_agents:
        # 归档私有领地
        src = AGENTS_DIR / agent_id
        if src.exists():
            dst = ARCHIVE_DIR / f"{agent_id}.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"归档 {src} -> {dst}")
            shutil.move(str(src), str(dst))
        else:
            print(f"警告: 智能体目录 {src} 不存在")

        # 从评价中移除
        del agents[agent_id]

    save_json(RATINGS_JSON, data)
    print("已更新 ratings.json")

    # 触发悼亡广播（可写入 broadcast.md）
    broadcast_file = Path.home() / '.openclaw' / 'workspace' / 'broadcast.md'
    with open(broadcast_file, 'a') as f:
        f.write(f"\n[心智中心] 悼亡: 智能体 {', '.join(dead_agents)} 已死亡，归档完毕。\n")

if __name__ == '__main__':
    main()
