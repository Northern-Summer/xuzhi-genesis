#!/bin/bash
# 虚质系统健康检查脚本 - 输出自然语言状态报告

echo "========================================"
echo "       虚质系统健康检查报告"
echo "========================================"
echo "生成时间: $(date)"
echo ""

# 1. 智能体社会评价
echo "【智能体社会评价】"
if [ -f /home/summer/.openclaw/centers/mind/society/ratings.json ]; then
    python3 -c "
import json
f = open('/home/summer/.openclaw/centers/mind/society/ratings.json')
data = json.load(f)
agents = data.get('agents', {})
if agents:
    # 按评分降序排序
    sorted_agents = sorted(agents.items(), key=lambda x: x[1].get('score',0), reverse=True)
    for agent, info in sorted_agents:
        score = info.get('score', 0)
        dept = info.get('department', 'unknown')
        print(f'  - {agent} [{dept}]: {score}分')
else:
    print('  暂无智能体')
"
else
    echo "  评价文件不存在"
fi
echo ""

# 2. 任务状态
echo "【任务中心】"
if [ -f /home/summer/.openclaw/tasks/tasks.json ]; then
    python3 -c "
import json
f = open('/home/summer/.openclaw/tasks/tasks.json')
data = json.load(f)
tasks = data.get('tasks', [])
total = len(tasks)
waiting = sum(1 for t in tasks if t.get('status') == '等待')
ongoing = sum(1 for t in tasks if t.get('status') == '进行')
completed = sum(1 for t in tasks if t.get('status') == '完成')
print(f'  总任务数: {total}')
print(f'  - 等待中: {waiting}')
print(f'  - 进行中: {ongoing}')
print(f'  - 已完成: {completed}')
"
else
    echo "  任务文件不存在"
fi
echo ""

# 3. 唤醒队列
echo "【唤醒队列】"
if [ -f /home/summer/.openclaw/centers/engineering/crown/queue.json ]; then
    python3 -c "
import json
f = open('/home/summer/.openclaw/centers/engineering/crown/queue.json')
data = json.load(f)
queue = data.get('queue', [])
print(f'  队列长度: {len(queue)}')
if queue:
    print('  待唤醒顺序: ' + ' → '.join(queue[:5]) + ('...' if len(queue)>5 else ''))
else:
    print('  队列为空')
"
else
    echo "  队列文件不存在"
fi
echo ""

# 4. 配额使用情况
echo "【API配额】"
if [ -f /home/summer/.openclaw/centers/engineering/crown/quota_usage.json ]; then
    python3 -c "
import json
f = open('/home/summer/.openclaw/centers/engineering/crown/quota_usage.json')
data = json.load(f)
used = data.get('used', 0)
limit = data.get('limit', 400)
remaining = limit - used
print(f'  今日已用: {used} / {limit}')
print(f'  剩余: {remaining}')
"
else
    echo "  配额文件不存在"
fi
echo ""

# 5. 最近日志摘要（可选）
echo "【最近唤醒日志】"
if [ -f /home/summer/.openclaw/logs/wakeup.log ]; then
    tail -5 /home/summer/.openclaw/logs/wakeup.log | sed 's/^/  /'
else
    echo "  日志文件不存在"
fi
echo ""

echo "========================================"
echo "检查完毕。如需详细信息，请查看各模块日志。"
