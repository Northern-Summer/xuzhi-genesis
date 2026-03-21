#!/usr/bin/env python3
"""
distill_lessons.py — 从反馈日志中蒸馏最有价值的教训，写入 lessons.json
每24小时由cron触发，或由任何Agent主动调用。
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

LOG_FILE = Path.home() / "xuzhi_genesis/centers/mind/society/feedback_log.jsonl"
LESSONS_FILE = Path.home() / "xuzhi_genesis/centers/mind/society/lessons.json"
MAX_LESSONS = 10

def load_log() -> list:
    if not LOG_FILE.exists():
        return []
    entries = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except:
                    pass
    return entries

def save_lessons(lessons: list):
    LESSONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_updated": datetime.now().isoformat(),
        "count": len(lessons),
        "lessons": lessons
    }
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data

def distill(lookback_hours=48) -> list:
    """从最近 lookback_hours 小时的反馈中提取教训"""
    entries = load_log()
    cutoff = datetime.now() - timedelta(hours=lookback_hours)
    recent = []
    for e in entries:
        try:
            dt = datetime.strptime(f"{e['date']} {e.get('time','00:00:00')}", "%Y-%m-%d %H:%M:%S")
            if dt >= cutoff:
                recent.append(e)
        except:
            pass

    # 按feedback类型加权：negative教训价值更高
    scored = []
    for e in recent:
        if e.get("lesson"):
            score = 3 if e["feedback"] == "negative" else 1
            scored.append((score, e["lesson"], e))
    
    # 按分数排序，取前MAX_LESSONS
    scored.sort(key=lambda x: -x[0])
    lessons = []
    seen = set()
    for score, lesson, entry in scored:
        # 去重，保留首个
        key = lesson[:60]
        if key not in seen:
            seen.add(key)
            lessons.append({
                "lesson": lesson,
                "from_agent": entry["agent"],
                "original_task": entry["task"],
                "feedback": entry["feedback"],
                "extracted_at": datetime.now().isoformat(),
                "confidence": score,
            })
        if len(lessons) >= MAX_LESSONS:
            break
    
    return lessons

if __name__ == "__main__":
    lessons = distill()
    result = save_lessons(lessons)
    print(f"✅ 蒸馏完成: {result['count']} 条教训 → {LESSONS_FILE}")
    for i, l in enumerate(lessons, 1):
        print(f"  {i}. [{l['from_agent']}] {l['lesson'][:80]}")
