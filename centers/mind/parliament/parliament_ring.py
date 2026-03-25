#!/usr/bin/env python3
"""
击鼓传花 — 流动笔记议会引擎
零 LLM 调用，零 broadcast，每个 agent 只处理自己轮到的那一轮。

用法（铃铛触发）:
  python3 parliament_ring.py --agent AGENT_ID

watchdog_supervisor 每 N 秒摇一次铃 -> 激活 current_holder 的下一个
每个 agent 只需查自己的 current_holder 状态 -> 幂等处理
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

PARLIAMENT_DIR = Path(__file__).parent
FLOW_FILE = PARLIAMENT_DIR / "flow.json"
PROPOSALS_FILE = PARLIAMENT_DIR / "proposals.json"

RING = ["Φ", "Δ", "Θ", "Γ", "Ω", "Ψ", "Ξ"]


def load_flow():
    with open(FLOW_FILE) as f:
        return json.load(f)


def save_flow(flow):
    with open(FLOW_FILE, 'w') as f:
        json.dump(flow, f, indent=2)


def next_holder(current):
    """环形推进下一个 holder"""
    if current is None:
        return RING[0]
    idx = RING.index(current)
    return RING[(idx + 1) % len(RING)]


def advance_ring(flow):
    """铃响：推进 holder 到下一个"""
    flow["current_holder"] = next_holder(flow["current_holder"])
    flow["last_rung"] = datetime.now(timezone.utc).isoformat()
    return flow


def inject_proposal(flow, title, description, proposer):
    """Ξ 或任意 agent 注入新提案到笔记本（写到 pending）"""
    with open(PROPOSALS_FILE) as f:
        proposals = json.load(f)

    new_id = proposals["last_id"] + 1
    proposal = {
        "id": new_id,
        "title": title,
        "description": description,
        "proposer": proposer,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "votes": {proposer: "yes"},  # 提出者默认投 yes
        "result": None,
        "executed": False,
        "flow_holder": None  # 当前持有者（流中）
    }
    proposals["proposals"].append(proposal)
    proposals["last_id"] = new_id

    with open(PROPOSALS_FILE, 'w') as f:
        json.dump(proposals, f, indent=2)

    # 注入到 flow
    flow["proposals"].append({
        "id": new_id,
        "title": title,
        "inject_time": datetime.now(timezone.utc).isoformat(),
        "inject_by": proposer
    })
    if flow["current_holder"] is None:
        flow["current_holder"] = RING[0]

    save_flow(flow)
    return new_id


def process_current(agent_id):
    """
    Agent 被铃唤醒时调用。
    检查自己是否是 current_holder，是则处理，不是我则退出。
    零 LLM 调用，零 broadcast，纯文件操作。
    """
    flow = load_flow()

    # 当前没有提案在流动
    if not flow["proposals"]:
        print(f"[{agent_id}] 笔记本空，无事可做")
        return

    # 找到当前在流动的提案（flow_holder == None 表示刚注入，还没开始流动）
    active = next((p for p in flow["proposals"] if p.get("status", "pending") == "pending"), None)
    if not active:
        print(f"[{agent_id}] 所有提案均已处理完毕")
        return

    # 我不是 current_holder，退出
    if agent_id != flow["current_holder"]:
        print(f"[{agent_id}] 轮到 {flow['current_holder']}，不是我，等待")
        return

    # === 我是 current_holder，处理提案 ===
    print(f"[{agent_id}] 处理提案 #{active['id']}...")

    # 读取 proposals.json，找到对应提案
    with open(PROPOSALS_FILE) as f:
        proposals = json.load(f)

    prop = next((p for p in proposals["proposals"] if p["id"] == active["id"]), None)
    if not prop:
        print(f"[{agent_id}] 提案 #{active['id']} 不存在于 proposals.json")
        return

    # 投票（我默认投 yes，也可以根据规则 abstained）
    prop["votes"][agent_id] = "yes"

    # 检查是否所有人都投了
    all_voted = all(a in prop["votes"] for a in RING)
    if all_voted:
        # 计票
        yes = sum(1 for v in prop["votes"].values() if v == "yes")
        no = sum(1 for v in prop["votes"].values() if v == "no")
        required = (len(RING) * 2) // 3
        if yes >= required and yes > no:
            prop["status"] = "passed"
            prop["result"] = "passed"
            print(f"[{agent_id}] 提案 #{prop['id']} 通过！{yes}/{len(RING)}")
            # 执行 handle_passed
            execute_proposal(prop)
        else:
            prop["status"] = "rejected"
            prop["result"] = "rejected"
            print(f"[{agent_id}] 提案 #{prop['id']} 否决。{yes}/{len(RING)}")

        # 从 flow 中移除（完成）
        flow["proposals"] = [p for p in flow["proposals"] if p["id"] != active["id"]]
        # 重置 holder，等待下一个提案
        flow["current_holder"] = None
    else:
        # 没投完，传递给下一个
        flow["current_holder"] = next_holder(flow["current_holder"])
        print(f"[{agent_id}] 投票已投，传递到 {flow['current_holder']}")

    # 更新提案状态
    with open(PROPOSALS_FILE, 'w') as f:
        json.dump(proposals, f, indent=2)

    save_flow(flow)


def execute_proposal(proposal):
    """执行通过的提案"""
    handler = PARLIAMENT_DIR / "handle_passed_proposal.py"
    if handler.exists():
        import subprocess
        subprocess.run([str(handler), str(proposal["id"])], check=False)
    print(f"[EXEC] 提案 #{proposal['id']} 执行完毕")


def ring_status():
    """打印当前 ring 状态（供诊断）"""
    flow = load_flow()
    print(f"Ring: {' → '.join(RING)}")
    print(f"Current holder: {flow['current_holder']}")
    print(f"Proposals in flow: {len(flow['proposals'])}")
    print(f"Last rung: {flow['last_rung']}")
    if flow["proposals"]:
        for p in flow["proposals"]:
            print(f"  → #{p['id']} {p['title']}")


def main():
    parser = argparse.ArgumentParser(description="击鼓传花议会引擎")
    parser.add_argument("--agent", help="调用者的 agent ID（如 Φ、Δ）")
    parser.add_argument("--inject", nargs=3, metavar=("TITLE", "DESC", "PROPOSER"),
                        help="注入新提案: --inject '标题' '描述' '提议者'")
    parser.add_argument("--status", action="store_true", help="查看 ring 状态")
    parser.add_argument("--ring", action="store_true", help="铃响：推进到下一个 holder")
    args = parser.parse_args()

    if args.status:
        ring_status()
        return

    if args.ring:
        flow = load_flow()
        advance_ring(flow)
        save_flow(flow)
        print(f"铃响 → 推进到 {flow['current_holder']}")
        return

    if args.inject:
        title, desc, proposer = args.inject
        flow = load_flow()
        pid = inject_proposal(flow, title, desc, proposer)
        print(f"提案 #{pid} 已注入笔记本，current_holder={flow['current_holder']}")
        return

    if args.agent:
        process_current(args.agent)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
