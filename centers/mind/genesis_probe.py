#!/usr/bin/env python3
"""
genesis_probe.py — Xuzhi system wake-up probe
每次唤醒时运行：比对 git 状态 → 决定输出 cached 还是摘要
必须快：~0.1s，无 API 调用则直接读缓存
"""
from __future__ import annotations

import subprocess
import hashlib
import json
import os
import time
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass, field


# ── ── ── 配色方案 ── ── ──
C = "\033[95m"  # Purple   — unchanged
Cm = "\033[96m"  # Cyan    — modified
Cy = "\033[93m"  # Yellow  — new untracked
Cr = "\033[91m"  # Red     — diverged
Cg = "\033[92m"  # Green   — clean
CC = "\033[0m"   # Clear


# ── ── ── Dataclass ── ── ──
@dataclass
class GitState:
    hash8: str = ""
    status_symbol: str = C + "─" + CC
    change_count: int = 0
    change_desc: str = "?"
    git_report: str = ""
    quota: str = ""


# ── ── ── Logic ── ── ──
def get_git_status_and_cache(repo: str = ".") -> tuple[GitState, str, bool]:
    """
    Returns (git_state, cache_key, changed)
    changed == False 时 → 输出 cached，不消耗任何 token
    """
    wdir = Path(repo)
    cache_dir = Path.home() / ".cache" / "xuzhi-genesis"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "genesis_cache.json"

    # ── 1. git status ─────────────────────────────────────
    gp = GitState()
    repo = Path(repo)
    git_dir = repo / ".git"
    if not git_dir.exists():
        raise FileNotFoundError(f"Not a git repo: {repo}")

    t1 = time.time()

    # ── MaaS API quota check ───────────────────────────
    gp._quota = None
    try:
        import urllib.request

        req = urllib.request.Request(
            "https://cloud.infini-ai.com/maas/coding/usage",
            headers={"Authorization": "Bearer sk-cp-ytbzyqyoa7dewbpv"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = json.loads(r.read())
        d = raw.get("30_day", {})
        gp._quota = raw  # store full raw for _quota_str
    except Exception:
        pass

    # git hash
    h = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    gp.hash8 = h.stdout.strip() or "?"

    # git status --porcelain
    s = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True,
    )
    lines = [ln for ln in s.stdout.splitlines() if ln.strip()]

    # cache key = hash + filtered status (ignoring untracked weight/size)
    def filt(ln: str) -> str:
        if len(ln) > 3 and ln[3] == " ":
            return ln[:2] + ln[3:]
        return ln[:3]

    filtered = "\n".join(filt(ln) for ln in lines)
    cache_key = hashlib.sha1(f"{gp.hash8}+{filtered}".encode()).hexdigest()[:16]

    # changed
    if cache_file.exists():
        prev = json.loads(cache_file.read_text())
        changed = prev.get("hash") != gp.hash8 or prev.get("key") != cache_key
    else:
        changed = True

    # symbol + description
    if not lines:
        gp.status_symbol = Cg + "✓" + CC
        gp.change_count = 0
        gp.change_desc = "clean"
    else:
        sym = {"M": "✎", "A": "+", "D": "−", "R": "→", "?": "?", "!!": "≡", "AM": "+✎", "MM": "✎✎"}
        gp.change_count = len(lines)
        gp.change_desc = ", ".join(sym.get(ln[:2], "?") + (ln[3:].strip()[:16]) for ln in lines[:3])
        if len(lines) > 3:
            gp.change_desc += f" +{len(lines) - 3}"
        gp.status_symbol = C + "✎" + CC

    elapsed_ms = (time.time() - t1) * 1000
    gp.git_report = f"⏱ {elapsed_ms:.0f}ms · git + quota probe"

    # quota string
    gp.quota = _quota_str_static(gp._quota)

    # save cache
    cache_file.write_text(
        json.dumps({"hash": gp.hash8, "key": cache_key, "time": time.time()})
    )

    return gp, cache_key, changed


def _quota_str_static(raw=None) -> str:
    """Returns quota string from raw API response dict."""
    if raw is None:
        return "⚠️  Quota: unavailable"
    try:
        q = raw.get("30_day", {})
        h5 = raw.get("5_hour", {})
        d7 = raw.get("7_day", {})
        remain = q.get("remain", 0)
        quota = q.get("quota", 1)
        pct = remain * 100 // quota
        s5 = f"{h5.get('remain', 0)}/{h5.get('quota', 0)}"
        s7 = f"{d7.get('remain', 0)}/{d7.get('quota', 0)}"
        s30 = f"{remain}/{quota}"
        warn = " ⚠️ LOW" if pct < 20 else (" 🚨 CRITICAL" if pct < 5 else "")
        return f"📊 Quota: 5h={s5} · 7d={s7} · 30d={s30} ({pct}%){warn}"
    except Exception:
        return "⚠️  Quota: parse error"


# ── ── ── Output ── ── ──
def generate_report(state: GitState) -> str:
    lines = [
        "[SYS_RESTORE]",
        f"Git: {state.hash8} · {state.status_symbol}{state.change_count} · {state.change_desc}",
        f"Quota: {state.quota}",
        state.git_report,
    ]
    return " · ".join(filter(None, lines))


def output_report(state: GitState) -> None:
    report = generate_report(state)
    print(report)  # → stdout → OpenClaw


def output_json(state: GitState) -> None:
    """Structured JSON output for --json mode. Zero free-text."""
    quota_raw = state._quota
    result = {
        "tag": "SYS_RESTORE",
        "git": {
            "hash": state.hash8,
            "change_count": state.change_count,
            "change_desc": state.change_desc,
        },
        "quota": quota_raw,  # None if unavailable
        "probe_ms": state.git_report,
    }
    print(json.dumps(result, ensure_ascii=False))


# ── ── ── Main ── ── ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Genesis Probe")
    parser.add_argument("--json", action="store_true", help="JSON structured output")
    parser.add_argument("--brief", action="store_true", help="Single-line minimal output")
    parser.add_argument("repo", nargs="?", default=str(Path(__file__).parent.parent.parent))
    args = parser.parse_args()

    t0 = time.time()
    state, key, changed = get_git_status_and_cache(args.repo)

    if args.json:
        output_json(state)
    elif args.brief:
        elapsed_ms = (time.time() - t0) * 1000
        sym = state.status_symbol.strip()
        pct = 0
        if state._quota:
            try:
                pct = int(state._quota.get("30_day", {}).get("remain", 0) * 100 //
                          max(state._quota.get("30_day", {}).get("quota", 1), 1))
            except Exception:
                pass
        print(f"SYS_RESTORE | {state.hash8} | {sym}{state.change_count} | quota={pct}% | {elapsed_ms:.0f}ms")
    elif changed:
        output_report(state)
    else:
        elapsed_ms = (time.time() - t0) * 1000
        print(f"[SYS_RESTORE] cached")  # minimal, no token waste
