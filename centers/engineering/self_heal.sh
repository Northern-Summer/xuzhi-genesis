#!/bin/bash
# self_heal.sh — Xuzhi系统自愈脚本 v2
# 职责：监视核心指标，发现异常自动修复，不需要人介入
# 由 Λ (工学部) 维护
# 使用方式：bash self_heal.sh [check|fix|full]
# 推荐：加入cron，每小时运行一次 self_heal.sh fix

LOG="$HOME/xuzhi_genesis/centers/engineering/self_heal.log"
GIT="$HOME/xuzhi_genesis"
SRC="$GIT/centers/intelligence/knowledge/knowledge.db"
MODE="${1:-full}"

log() { echo "[$(date +%H:%M:%S)] $1" | tee -a $LOG; }

# ── 0. API 配额检测（每次运行必须首先执行）──────────────
# MaaS API: 5h=5000, 7d=6000, 30d=12000
# 策略：剩余 <20% 时降低研究密度，<5% 时暂停 AutoRA，仅保留心跳
check_quota() {
    local raw
    raw=$(curl -s -X GET 'https://cloud.infini-ai.com/maas/coding/usage' \
        --header 'Authorization: Bearer sk-cp-ytbzyqyoa7dewbpv' 2>/dev/null)
    if [ -z "$raw" ]; then
        log "⚠️  Quota: 无法获取，假设充足"
        return 0
    fi
    local remain_30d
    remain_30d=$(echo "$raw" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('30_day',{}).get('remain',0))" 2>/dev/null || echo 0)
    local quota_30d
    quota_30d=$(echo "$raw" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('30_day',{}).get('quota',1))" 2>/dev/null || echo 1)
    local pct=$((remain_30d * 100 / quota_30d))
    log "📊 API配额: ${remain_30d}/${quota_30d} (${pct}%)"
    if [ "$pct" -lt 5 ]; then
        log "🚨 配额<5%: 暂停AutoRA，仅保留心跳"
        echo "$raw" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for j in d.get('jobs',[]):
    n=j.get('name','')
    if 'AutoRA' in n or 'Research' in n or '研究' in n:
        print('PAUSE:'+j.get('id','?'))
" 2>/dev/null
    elif [ "$pct" -lt 20 ]; then
        log "⚠️  配额<20%: 降低研究密度"
    fi
}

# ── 1. Cron JSON 解析助手 ────────────────────────────────
get_cron_raw() {
    openclaw cron list 2>/dev/null | awk '/RAW JSON/,0' | tail -n +2 2>/dev/null
}

# ── 1. Cron 检测 + 自动修复 ──────────────────────────────
fix_cron() {
    local raw=$(get_cron_raw)
    if [ -z "$raw" ]; then
        log "⚠️  Cron: 无法获取列表"
        return 0
    fi
    local total=$(echo "$raw" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('jobs',[])))" 2>/dev/null || echo 0)
    local enabled=$(echo "$raw" | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for j in d.get('jobs',[]) if j.get('enabled',True)))" 2>/dev/null || echo 0)
    log "Cron: $enabled/$total 启用"
    if [ "$total" -eq 0 ]; then
        log "🚨 Cron: 0任务，紧急重建"
        return 1
    fi
    if [ "$enabled" -lt "$total" ]; then
        log "⚠️  启用 $((total-enabled)) 个禁用任务..."
        echo "$raw" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for j in d.get('jobs',[]):
    if not j.get('enabled', True):
        print(j.get('id','?'))
" 2>/dev/null | while read jid; do
            openclaw cron update "\$jid" --enabled 2>/dev/null
        done
        log "✅ 禁用任务已重新启用"
    fi
}

# ── 2. 知识库检测 ────────────────────────────────────────
check_knowledge() {
    local count=$(sqlite3 "$SRC" "SELECT COUNT(*) FROM entities;" 2>/dev/null || echo 0)
    if [ "$count" -lt 200 ]; then
        log "🚨 知识库: 仅 $count entities，触发采集"
        cd "$GIT/centers/intelligence" && python3 seed_collector.py 2>/dev/null &
        return 1
    fi
    log "✅ 知识库: $count entities"
}

# ── 3. Harness 测试 ─────────────────────────────────────
check_tests() {
    local result
    result=$(cd "$GIT/centers/engineering/harness" && python3 -m pytest tests/ -q 2>&1 | tail -1)
    if echo "$result" | grep -q "passed"; then
        log "✅ Tests: $result"
    else
        log "⚠️  Tests: $result"
    fi
}

# ── 4. Git auto-push ─────────────────────────────────────
check_git_push() {
    cd "$GIT"
    local ahead=$(git status -s 2>/dev/null | wc -l)
    if [ "$ahead" -gt 0 ]; then
        git add -A
        git commit -m "Auto: $(date +%Y-%m-%d_%H:%M)" 2>/dev/null
        git push origin master 2>/dev/null
        log "✅ Git: $ahead 文件已推送"
    else
        log "✅ Git: 无待推送"
    fi
}

# ── 5. 磁盘空间 ─────────────────────────────────────────
check_disk() {
    local pct=$(df -h ~ | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$pct" -gt 85 ]; then
        log "🚨 磁盘: ${pct}% used (> 85%)"
    else
        log "✅ 磁盘: ${pct}% used"
    fi
}

# ── 6. 今日memory文件 ───────────────────────────────────
check_memory_today() {
    local today=$(date +%Y-%m-%d)
    local daily="$HOME/.openclaw/workspace/memory/$today.md"
    if [ ! -f "$daily" ]; then
        mkdir -p "$(dirname $daily)"
        echo "# $today Daily Log\n\n" > "$daily"
        log "✅ 已创建 $daily"
    fi
}

# ── 主程序 ──────────────────────────────────────────────
log "=== 自愈检查 [$(date +%Y-%m-%d_%H:%M)] ==="
check_quota  # 必须最先执行
case "$MODE" in
    check)
        fix_cron
        check_knowledge
        ;;
    fix)
        fix_cron
        check_knowledge
        check_disk
        ;;
    full)
        fix_cron
        check_knowledge
        check_tests
        check_git_push
        check_disk
        check_memory_today
        ;;
esac
log "=== 完成 ==="
