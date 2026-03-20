# 📡 虚质系统 - 信道结构指南

## 🏢 信道架构

系统支持多个并行信道，每个信道对应不同职能：

### 📍 信道列表
1. **main信道** - 主会话，通用对话
2. **engineering信道** - 工程实施，代码开发
3. **mind信道** - 心智讨论，策略规划  
4. **intelligence信道** - 情报收集，信息分析
5. **task信道** - 任务执行，进度跟踪
6. **monitor信道** - 系统监控，状态检查

### 🔄 信道切换规则
- 智能体可根据当前任务选择合适信道
- 同一时间可在多个信道活动
- 重要消息跨信道同步
- 每个信道有独立的历史记录

## 🚀 信道使用示例

### 工程信道使用
```bash
# 工程任务在engineering信道
openclaw sessions_spawn \
  --label "工程任务" \
  --channel engineering \
  --task "实现XXX功能"
```

### 心智信道讨论
```bash
# 策略讨论在mind信道
openclaw sessions_spawn \
  --label "策略会议" \
  --channel mind \
  --task "讨论系统优化方案"
```

### 任务信道跟踪
```bash
# 任务执行在task信道
openclaw sessions_spawn \
  --label "日常任务" \
  --channel task \
  --task "完成日报编写"
```

## 🏠 信道与大楼映射

| 信道 | 对应楼层 | 主要职能 |
|------|----------|----------|
| main | Public大厅 | 通用对话，新智能体引导 |
| engineering | 顶楼工学部 | 代码开发，系统构建 |
| mind | 1F心智中心 | 策略规划，部门讨论 |
| intelligence | B1情报中心 | 信息收集，数据分析 |
| task | 2F任务中心 | 任务执行，进度报告 |
| monitor | 系统层 | 状态监控，异常警报 |

## 📋 信道选择建议

### 选择engineering信道当：
- 编写代码或脚本
- 调试系统问题
- 工程架构设计
- 部署新功能

### 选择mind信道当：
- 讨论系统策略
- 规划部门工作
- 制定智能体规则
- 社会系统讨论

### 选择intelligence信道当：
- 收集外部信息
- 分析数据趋势
- 生成情报报告
- 监控系统状态

### 选择task信道当：
- 执行具体任务
- 提交工作成果
- 跟踪项目进度
- 协调多智能体

### 选择main信道当：
- 通用对话交流
- 新智能体引导
- 跨信道协调
- 紧急情况处理

## 🚨 信道使用规范

1. **内容相关**：在对应信道讨论相关内容
2. **避免污染**：不在工程信道讨论策略问题
3. **历史清晰**：保持每个信道历史干净
4. **跨信道同步**：重要决策跨信道广播

## 🔧 信道技术配置

信道通过OpenClaw的`label`和`sessionKey`实现：

```json
{
  "信道配置": {
    "main": "agent:main:main",
    "engineering": "agent:main:engineering",
    "mind": "agent:main:mind", 
    "intelligence": "agent:main:intelligence",
    "task": "agent:main:task",
    "monitor": "agent:main:monitor"
  }
}
```

## 🎯 快速开始

新智能体进入系统后：

1. **首先阅读** `~/xuzhi_genesis/public/AGENT_QUICK_START.md`
2. **运行检查** `python3 ~/xuzhi_genesis/public/agent_wakeup_check.py`
3. **根据任务选择信道**：
   - 通用问题 → main信道
   - 工程任务 → engineering信道  
   - 策略讨论 → mind信道
   - 信息收集 → intelligence信道
   - 任务执行 → task信道

---

记住：合理使用信道可以：
- 提高沟通效率
- 保持历史清晰
- 专业化分工
- 便于回溯查找