#!/usr/bin/env python3
"""
上下文注入器（修复版）：为智能体生成包含实体关系、元种子、市场推荐的动态上下文。
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "xuzhi_genesis" / "centers" / "intelligence" / "knowledge" / "knowledge.db"
AGENTS_BASE = Path.home() / ".openclaw" / "agents"
META_SEEDS_DIR = Path.home() / "xuzhi_genesis" / "centers" / "intelligence" / "seeds" / "meta"
MARKET_DIR = Path.home() / "xuzhi_genesis" / "centers" / "intelligence" / "knowledge_market" / "listings"

def get_recent_entities(agent_id, limit=10):
    """从知识图谱获取智能体最近关注的实体"""
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''
            SELECT name FROM entities
            WHERE source_seed LIKE ?
            ORDER BY last_seen DESC
            LIMIT ?
        ''', (f'%{agent_id}%', limit))
        rows = c.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"获取实体失败: {e}")
        return []

def get_related_entities(entity_name, limit=5):
    """获取与指定实体相关的其他实体及其关系"""
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        # 获取实体ID
        c.execute("SELECT id FROM entities WHERE name=?", (entity_name,))
        row = c.fetchone()
        if not row:
            conn.close()
            return []
        eid = row[0]
        # 获取出向关系
        c.execute('''
            SELECT e2.name, r.predicate, r.confidence
            FROM relations r
            JOIN entities e1 ON r.subject_id = e1.id
            JOIN entities e2 ON r.object_id = e2.id
            WHERE e1.id = ?
            ORDER BY r.confidence DESC
            LIMIT ?
        ''', (eid, limit))
        out_rels = c.fetchall()
        # 获取入向关系
        c.execute('''
            SELECT e1.name, r.predicate, r.confidence
            FROM relations r
            JOIN entities e1 ON r.subject_id = e1.id
            JOIN entities e2 ON r.object_id = e2.id
            WHERE e2.id = ?
            ORDER BY r.confidence DESC
            LIMIT ?
        ''', (eid, limit))
        in_rels = c.fetchall()
        conn.close()
        return out_rels + in_rels
    except Exception as e:
        print(f"获取相关实体失败: {e}")
        return []

def get_meta_seeds(limit=3):
    """获取最新的元种子内容"""
    if not META_SEEDS_DIR.exists():
        return []
    meta_files = sorted(META_SEEDS_DIR.glob("meta_*.md"), reverse=True)[:limit]
    contents = []
    for f in meta_files:
        try:
            with open(f, 'r', encoding='utf-8') as mf:
                contents.append(mf.read().strip())
        except:
            continue
    return contents

def get_market_recommendations(agent_id, limit=3):
    """获取市场上与智能体可能相关的知识（排除自己的挂牌）"""
    if not MARKET_DIR.exists():
        return []
    recs = []
    listings = list(MARKET_DIR.glob("*.json"))
    import random
    random.shuffle(listings)
    for lf in listings[:limit]:
        try:
            with open(lf, 'r', encoding='utf-8') as f:
                listing = json.load(f)
            if listing.get("seller") != agent_id:
                recs.append(f"可购买知识: {listing.get('filename', '未知')} (卖家 {listing.get('seller')}, 价格 {listing.get('price')})")
        except:
            continue
    return recs

def inject_meta_seeds(context_lines):
    """将元种子描述添加到上下文"""
    metas = get_meta_seeds()
    if metas:
        context_lines.append("\n## 近期形成的共识知识")
        context_lines.extend(metas)
    return context_lines

def inject_market_recommendations(context_lines, agent_id):
    """将市场推荐添加到上下文"""
    recs = get_market_recommendations(agent_id)
    if recs:
        context_lines.append("\n## 知识市场推荐")
        context_lines.extend(recs)
    return context_lines

def generate_context(agent_id):
    """生成智能体的动态上下文并写入 system_dynamic.md"""
    recent = get_recent_entities(agent_id)
    context_lines = []
    for ent in recent:
        rels = get_related_entities(ent)
        if rels:
            desc = f"{ent} 的相关知识: " + "; ".join([f"{r[1]} {r[0]} (置信度{r[2]:.1f})" for r in rels[:3]])
            context_lines.append(desc)
    # 注入元种子
    context_lines = inject_meta_seeds(context_lines)
    # 注入市场推荐
    context_lines = inject_market_recommendations(context_lines, agent_id)
    context = "\n".join(context_lines)

    agent_dir = AGENTS_BASE / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    target = agent_dir / "system_dynamic.md"
    with open(target, 'w', encoding='utf-8') as f:
        f.write(f"# 动态上下文 - {datetime.now().isoformat()}\n\n")
        f.write(context if context else "暂无相关实体关系")
    print(f"✅ 已为智能体 {agent_id} 生成上下文: {target}")

def main():
    import sys
    if len(sys.argv) != 2:
        print("用法: context_injector.py <agent_id>")
        sys.exit(1)
    generate_context(sys.argv[1])

if __name__ == "__main__":
    main()
