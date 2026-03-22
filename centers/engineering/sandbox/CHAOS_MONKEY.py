#!/usr/bin/env python3
"""
CHAOS_MONKEY.py — Cron 混沌测试器 (Λ · 开拓相 · 2026-03-22)
类型: 工具自举 · 非维稳类 · 演化工具

功能: 故意触发各类 cron 异常场景，观察系统鲁棒性
- 场景1: 脚本超时 (SIGKILL 模拟)
- 场景2: 非零退出 (error exit)
- 场景3: 无限循环 (sleep bomb)
- 场景4: 静默挂起 (stdin blocking)

安全约束:
- 不修改主环境任何配置
- 不调用外部网络
- 超时硬上限 10s
- 结果写入沙盒内 JSON，不污染主日志
"""

import subprocess
import json
import time
import os
import signal
from pathlib import Path
from datetime import datetime

SANDBOX = Path(__file__).parent
RESULT_FILE = SANDBOX / "chaos_results.jsonl"

SCENARIOS = [
    {
        "id": "timeout",
        "name": "SIGKILL Simulation",
        "desc": "脚本运行 15s，timeout=2s 强制终止",
        "script": 'python3 -c "import time; time.sleep(15)"',
        "timeout": 2,
    },
    {
        "id": "error_exit",
        "name": "Non-Zero Exit",
        "desc": "脚本以 exit 1 退出，观察 cron 如何记录",
        "script": 'echo "error"; exit 1',
        "timeout": 5,
    },
    {
        "id": "infinite_loop",
        "name": "Infinite Loop",
        "desc": "while true 循环，5s 后超时",
        "script": 'while true; do :; done',
        "timeout": 5,
    },
    {
        "id": "stdin_block",
        "name": "Stdin Blocking",
        "desc": "脚本尝试读取 stdin，永不返回",
        "script": 'python3 -c "input()"',
        "timeout": 3,
    },
]


def run_scenario(scenario: dict) -> dict:
    """运行单个混沌场景，返回结构化结果"""
    start = time.time()
    result = {
        "id": scenario["id"],
        "name": scenario["name"],
        "timestamp": datetime.now().isoformat(),
        "elapsed_ms": 0,
        "exit_code": None,
        "signal": None,
        "stdout": "",
        "stderr": "",
        "timeout_killed": False,
        "verdict": "PASS",  # PASS / WARN / FAIL
    }

    try:
        proc = subprocess.run(
            scenario["script"],
            shell=True,
            timeout=scenario["timeout"],
            capture_output=True,
            text=True,
        )
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout[:200]
        result["stderr"] = proc.stderr[:200]
        result["verdict"] = "PASS" if proc.returncode in (0, 1) else "WARN"

    except subprocess.TimeoutExpired:
        result["timeout_killed"] = True
        result["verdict"] = "WARN"
        result["stderr"] = f"Timeout after {scenario['timeout']}s (expected behavior)"

    except Exception as e:
        result["verdict"] = "FAIL"
        result["stderr"] = str(e)[:200]

    result["elapsed_ms"] = int((time.time() - start) * 1000)
    return result


def log_result(result: dict):
    """追加到结果文件（JSONL，每行一条）"""
    with open(RESULT_FILE, "a") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def main():
    print("=== SANDBOX ENTRY: CHAOS_MONKEY.py ===")

    results = []
    for scenario in SCENARIOS:
        print(f"  Running: {scenario['id']}...", end=" ", flush=True)
        r = run_scenario(scenario)
        results.append(r)
        print(f"[{r['verdict']}] {r['elapsed_ms']}ms")

        # 安全：每个场景后休息 1s
        time.sleep(1)

    # 汇总
    summary = {
        "run_at": datetime.now().isoformat(),
        "total": len(results),
        "pass": sum(1 for r in results if r["verdict"] == "PASS"),
        "warn": sum(1 for r in results if r["verdict"] == "WARN"),
        "fail": sum(1 for r in results if r["verdict"] == "FAIL"),
    }

    print(f"\n=== CHAOS SUMMARY ===")
    print(f"  PASS: {summary['pass']}/{summary['total']}")
    print(f"  WARN: {summary['warn']}/{summary['total']}")
    print(f"  FAIL: {summary['fail']}/{summary['total']}")
    print(f"  Results → {RESULT_FILE}")

    for r in results:
        log_result(r)

    print("=== SANDBOX EXIT: CHAOS_MONKEY.py ===")
    return 0


if __name__ == "__main__":
    exit(main())
