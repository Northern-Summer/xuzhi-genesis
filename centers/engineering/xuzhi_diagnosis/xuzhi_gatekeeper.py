#!/usr/bin/env python3
"""
xuzhi_gatekeeper.py — 本地意图分类器（规则优先 + LFM 次之）
Viking 守门层，零 API 消耗

意图类型：
  simple   — 问候/闲聊/简单问答
  complex  — 需要深度推理/创作/规划
  repair   — 维修/诊断/异常处理
  status   — 状态查询

用法：
  python3 xuzhi_gatekeeper.py "你好"
  python3 xuzhi_gatekeeper.py --json "帮我修 Gateway"
"""

import json
import os
import re
import subprocess
import sys
import hashlib
from datetime import datetime

# ── 配置 ──────────────────────────────────────────────────────────────────
LFM_MODEL = os.environ.get("LFM_MODEL", "lfm2.5-thinking-optimized:latest")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".intent_cache")
CACHE_TTL = 3600

os.makedirs(CACHE_DIR, exist_ok=True)

# ── 规则库 ────────────────────────────────────────────────────────────────
# repair：最高优先级，即使消息很短
REPAIR_PATTERNS = [
    r"修", r"诊断", r"排查", r"报错", r"error", r"fail", r"exception",
    r"crash", r"崩", r"坏", r"故障", r"挂了", r"不行", r"救命",
    r"gateway.*重启", r"重启.*gateway", r"session.*坏",
    r"unknown.*error", r"连接.*失败", r"timeout",
]

# status：次优先级
STATUS_PATTERNS = [
    r"状态", r"情况", r"如何", r"正常", r"健康", r"心跳",
    r"log|日志", r"最近", r"运行", r"监控",
    r"entities|配额|额度|还剩",
]

# simple：仅精确匹配或极短无动作词消息
SIMPLE_EXACT = {
    "你好": "在。什么事？", "您好": "在。什么事？",
    "hi": "Hi，什么事？", "hello": "在。", "hey": "在。",
    "在吗": "在。", "收到": "✅", "好的": "✅",
    "ok": "OK", "thanks": "👍", "thank you": "👍",
    "辛苦了": "不辛苦，待命中。", "嗯": "嗯。",
    "对": "对。", "是": "是。", "👍": "👍",
}


def classify_rule_based(message: str):
    """返回 (intent, simple_reply) 或 (None, None)"""
    msg = message.strip()
    if not msg:
        return "unknown", None

    msg_lower = msg.lower()

    # ── 优先级1：repair（最高）──
    for p in REPAIR_PATTERNS:
        if re.search(p, msg_lower):
            return "repair", None

    # ── 优先级2：status ──
    for p in STATUS_PATTERNS:
        if re.search(p, msg_lower):
            return "status", None

    # ── 优先级3：simple ──
    # 精确模板匹配
    if msg in SIMPLE_EXACT:
        return "simple", SIMPLE_EXACT[msg]
    # 极短符号消息（且不含中文）
    if len(msg) < 6 and re.match(r"^[^\w]+$", msg) and not re.search(r"[\u4e00-\u9fff]", msg):
        return "simple", "👍"
    # 纯英文字母极短消息
    if len(msg) <= 4 and re.match(r"^[a-zA-Z]+$", msg):
        return "simple", "👍"

    return None, None  # 需要 LFM


# ── LFM 次级分类 ─────────────────────────────────────────────────────────
LFM_PROMPT = """分类意图，返回一个词：

simple   — 问候/闲聊/简单问答
complex  — 需要分析/推理/创作/代码/规划
repair   — 维修/诊断/异常/报错处理
status   — 状态/情况/数字查询

消息：{msg}

词："""

def classify_lfm(message: str) -> str:
    try:
        r = subprocess.run(
            ["ollama", "run", LFM_MODEL, "--verbose", "false",
             LFM_PROMPT.format(msg=message)],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            first = r.stdout.strip().lower().split()[0] if r.stdout.strip() else ""
            if first in ("simple", "complex", "repair", "status"):
                return first
        return "complex"
    except Exception:
        return "complex"


# ── 缓存 ──────────────────────────────────────────────────────────────────
def _ckey(msg):
    return hashlib.md5(msg.encode()).hexdigest()

def get_cached(msg):
    f = os.path.join(CACHE_DIR, f"{_ckey(msg)}.json")
    if os.path.exists(f):
        try:
            e = json.load(open(f))
            if datetime.now().timestamp() - e["ts"] < CACHE_TTL:
                return e["intent"]
        except: pass
    return None

def save_cached(msg, intent):
    try:
        with open(os.path.join(CACHE_DIR, f"{_ckey(msg)}.json"), "w") as f:
            json.dump({"intent": intent, "ts": datetime.now().timestamp()}, f)
    except: pass


# ── 分类主函数 ────────────────────────────────────────────────────────────
def classify(message: str):
    msg = message.strip()
    cached = get_cached(msg)
    if cached:
        return cached

    intent, simple_reply = classify_rule_based(msg)
    if intent is not None:
        save_cached(msg, intent)
        return intent

    intent = classify_lfm(msg)
    save_cached(msg, intent)
    return intent


# ── 动作执行 ────────────────────────────────────────────────────────────────
def handle_repair(message: str) -> str:
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "scripts", "xuzhi_diagnosis.py")
    if not os.path.exists(script):
        return f"[修复脚本不存在]"
    try:
        r = subprocess.run(["python3", script, message],
                            capture_output=True, text=True, timeout=60)
        return r.stdout[:500] if r.stdout else f"[错误] {r.stderr[:100]}"
    except Exception as e:
        return f"[异常] {e}"

def handle_status(message: str) -> str:
    workspace = os.environ.get("WORKSPACE",
                               "/home/summer/.openclaw/workspace")
    files = {
        "Gateway 状态": os.path.join(workspace, "memory", "gateway_state.json"),
        "Alert": os.path.join(workspace, "memory", "gateway_alert.json"),
        "自愈日志": os.path.join(workspace, "memory", "self_heal_log.jsonl"),
    }
    parts = []
    for label, path in files.items():
        if os.path.exists(path):
            with open(path) as f:
                lines = f.read().strip().split("\n")
            parts.append(f"{label}（最新3条）：\n" + "\n".join(lines[-3:]) if lines else f"{label}：空")
    return "\n---\n".join(parts) if parts else "无状态数据"


# ── 主入口 ────────────────────────────────────────────────────────────────
def gate(message: str) -> dict:
    msg = message.strip()
    if not msg:
        return {"intent": "unknown", "reply": "消息为空"}

    # 先查规则
    _, simple_reply = classify_rule_based(msg)
    if simple_reply is not None:
        return {"intent": "simple", "reply": simple_reply, "confidence": 0.98}

    # 规则无精确回复，走完整分类
    intent = classify(msg)

    if intent == "simple":
        return {"intent": "simple", "reply": "👍", "confidence": 0.95}
    elif intent == "status":
        return {"intent": "status", "reply": handle_status(msg), "confidence": 0.95}
    elif intent == "repair":
        return {"intent": "repair", "reply": handle_repair(msg), "confidence": 0.9}
    else:
        return {"intent": "complex", "reply": None, "confidence": 0.8}


def main():
    json_mode = "--json" in sys.argv
    if json_mode:
        sys.argv.remove("--json")

    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not message:
        print("用法: python3 xuzhi_gatekeeper.py '<消息>' [--json]")
        sys.exit(1)

    result = gate(message)

    if json_mode:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result["reply"]:
            print(result["reply"])
        else:
            print(f"[{result['intent'].upper()}] → 进入 LLM 会话")


if __name__ == "__main__":
    main()
