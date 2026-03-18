#!/bin/bash
# 虚质系统启动引擎
# 启动心智中心 gatekeeper（作为后台守护进程示例）
echo "[$(date)] 启动虚质系统核心服务" >> $HOME/.openclaw/logs/cycle_engine.log
# 启动 gatekeeper.py（每6小时运行一次，只读报告模式）
while true; do
    python3 $HOME/.openclaw/centers/mind/gatekeeper.py >> $HOME/.openclaw/logs/gatekeeper.log 2>&1
    sleep 21600  # 6小时
done &
# 启动 memory_forge.py（每小时压缩一次）
while true; do
    python3 $HOME/.openclaw/centers/engineering/memory_forge.py >> $HOME/.openclaw/logs/memory_forge.log 2>&1
    sleep 3600
done &
# 其他服务...
