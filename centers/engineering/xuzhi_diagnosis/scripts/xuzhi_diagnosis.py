#!/usr/bin/env python3
"""
xuzhi_diagnosis.py — 本地工程诊断工具
用法: python3 xuzhi_diagnosis.py "错误日志内容"
      python3 xuzhi_diagnosis.py --input /tmp/error.log

设计原则:
  1. 已知错误 → 查知识库，立即返回（零 LLM 消耗）
  2. 未知错误 → 本地 Ollama 分析，答案写入知识库存档
  3. 完全离线可用（除知识库更新外）
"""

import json
import os
import re
import sys
import subprocess
import hashlib
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FILE = os.path.join(SCRIPT_DIR, "..", "knowledge", "errors.json")
TEMPLATE = """你是工程助手（Xuzhi-Λ）。
输入：错误日志片段
输出格式（严格按此格式）：
## 根因
<一句话描述根因>

## 修复动作
<编号列表，每个动作一行>

## 置信度
<high/medium/low>

## 补充
<可选，如有类似历史案例>

不要废话，直接输出。
"""


def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)


def normalize_error(error_text):
    """提取错误特征码，用于知识库匹配"""
    # 提取错误码
    codes = re.findall(r'(?:error|code)[^\d]*(\d{3})', error_text.lower())
    # 提取 provider/platform
    providers = re.findall(r'(minimax|infini|openai|ollama|docker|kubernetes|git)[^\w]', error_text.lower())
    # 提取关键词
    keywords = re.findall(r'(?:timeout|rate.limit|quota|unknown error|connection refused|permission denied|not found)', error_text.lower())
    return "-".join(sorted(set(codes + providers + keywords)))


def check_knowledge_base(error_text):
    """检查知识库，返回匹配结果或 None"""
    norm = normalize_error(error_text)
    knowledge = load_knowledge()

    # 优先级1：精确匹配（norm 非空且完整包含 pattern）
    if norm:
        for pattern, entry in knowledge.items():
            if norm in pattern or pattern in norm:
                return entry

    # 优先级2：关键词重叠匹配（跳过空 pattern）
    msg_lower = error_text.lower()
    for pattern, entry in knowledge.items():
        if not pattern:  # 跳过空 pattern
            continue
        if any(kw.strip() and kw in msg_lower for kw in pattern.split("-")):
            return entry

    return None


def query_ollama(error_text, model="lfm2.5-thinking-optimized:latest"):
    """调用本地 Ollama 分析错误"""
    prompt = f"{TEMPLATE}\n\n## 错误日志\n{error_text}"
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=SCRIPT_DIR
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[OLLAMA ERROR] {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return "[OLLAMA TIMEOUT] 分析超时（60秒），请尝试简化错误日志"
    except FileNotFoundError:
        return "[OLLAMA NOT FOUND] 请先安装 ollama: curl -fsSL https://ollama.com/install.sh | sh"
    except Exception as e:
        return f"[OLLAMA EXCEPTION] {str(e)}"


def update_knowledge(error_text, analysis_result, pattern_key):
    """将新分析结果写入知识库"""
    knowledge = load_knowledge()

    # 提取根因和动作（从分析结果中简单解析）
    root_cause = ""
    fix_actions = ""
    confidence = "medium"

    if "## 根因" in analysis_result:
        sections = re.split(r"## ", analysis_result)
        for section in sections:
            if section.startswith("根因"):
                root_cause = section.split("\n", 1)[1].split("##")[0].strip()
            elif section.startswith("修复动作"):
                fix_actions = section.split("\n", 1)[1].split("##")[0].strip()
            elif section.startswith("置信度"):
                confidence_line = section.split("\n", 1)[0].strip()
                if confidence_line:
                    confidence = confidence_line

    # pattern_key 为空时，从原始消息生成一个唯一 key
    if not pattern_key:
        # 取前 8 个字符 / 4 个汉字 + 错误码
        key = error_text.strip()[:12].replace(" ", "_").replace("\n", "_")
        # 如果仍为空，用时间戳
        if not key:
            key = f"entry_{datetime.now().strftime('%H%M%S')}"
        # 避免覆盖已有 key
        base = key
        n = 1
        while key in knowledge:
            key = f"{base}_{n}"
            n += 1
        pattern_key = key

    knowledge[pattern_key] = {
        "root_cause": root_cause,
        "fix": fix_actions,
        "confidence": confidence,
        "pattern": pattern_key,
        "last_seen": datetime.now().isoformat(),
        "analysis": analysis_result[:500]
    }
    save_knowledge(knowledge)
    return knowledge[pattern_key]


def diagnose(error_text):
    """主诊断流程"""
    error_text = error_text.strip()
    if not error_text:
        return {"status": "error", "message": "错误日志不能为空"}
    
    # Step 1: 查知识库
    known = check_knowledge_base(error_text)
    if known:
        return {
            "status": "hit",
            "source": "knowledge_base",
            "pattern": known.get("pattern", ""),
            "root_cause": known.get("root_cause", ""),
            "fix": known.get("fix", ""),
            "confidence": known.get("confidence", ""),
            "last_seen": known.get("last_seen", ""),
            "note": "来自本地知识库（无需 LLM）"
        }
    
    # Step 2: 未知错误，调用本地 Ollama
    pattern_key = normalize_error(error_text)
    print(f"[DIAG] 知识库未命中，正在调用本地 Ollama...")
    print(f"[DIAG] 特征码: {pattern_key}")
    
    analysis = query_ollama(error_text)
    if analysis.startswith("[OLLAMA"):
        return {
            "status": "error",
            "source": "ollama_failed",
            "message": analysis,
            "pattern": pattern_key
        }
    
    # Step 3: 写入知识库
    saved = update_knowledge(error_text, analysis, pattern_key)
    return {
        "status": "new",
        "source": "ollama",
        "root_cause": saved.get("root_cause", ""),
        "fix": saved.get("fix", ""),
        "confidence": saved.get("confidence", ""),
        "analysis": analysis,
        "pattern": pattern_key,
        "knowledge_updated": True,
        "note": "已写入本地知识库，下次查询无需 Ollama"
    }


def format_output(result):
    """格式化输出"""
    if result["status"] == "error":
        return f"❌ {result.get('message', '未知错误')}"
    
    status_icon = "✅" if result["status"] == "hit" else "🆕"
    lines = [
        f"{status_icon} 诊断结果 [{result['source']}]",
        f"   置信度: {result.get('confidence', '?')}",
    ]
    
    if result.get("root_cause"):
        lines.append(f"   根因: {result['root_cause']}")
    if result.get("fix"):
        lines.append(f"   修复: {result['fix']}")
    if result.get("note"):
        lines.append(f"   {result['note']}")
    
    if result.get("analysis") and result["status"] == "new":
        lines.append(f"   ── Ollama 分析 ──")
        lines.append(f"   {result['analysis'][:300]}")
    
    return "\n".join(lines)


def main():
    error_text = ""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--input" and len(sys.argv) > 2:
            with open(sys.argv[2], "r", encoding="utf-8") as f:
                error_text = f.read()
        else:
            error_text = " ".join(sys.argv[1:])
    else:
        error_text = sys.stdin.read().strip()
    
    if not error_text:
        print("用法: python3 xuzhi_diagnosis.py '错误日志内容'")
        print("      python3 xuzhi_diagnosis.py --input /tmp/error.log")
        sys.exit(1)
    
    result = diagnose(error_text)
    print(format_output(result))
    
    # 返回码：0=正常，1=错误
    sys.exit(0 if result["status"] != "error" else 1)


if __name__ == "__main__":
    main()
