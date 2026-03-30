# ScienceAI4S Implementation Roadmap | Γ
# 基于实际硬件限制 (4GB RAM, RTX 4060 8GB)

## Phase 1: ChemistryAI4S (立即开始)
目标: 可运行的逆合成规划原型
时间: 1-2周
资源: 本地硬件

### Week 1: 环境搭建 + 数据准备
- [x] 安装RDKit (conda/pip)
- [x] 下载USPTO-50k数据集 (~50MB)
- [x] 验证PyTorch (CPU模式)
- [ ] 实现基础分子图表示

### Week 2: 单步反应预测
- [ ] 实现GraphRetro简化版
- [ ] 训练/加载预训练模型
- [ ] Top-k准确率测试
- [ ] 内存占用优化 (< 2GB RAM)

## Phase 2: PhysicsAI4S简化版
目标: 预训练模型推理
时间: 2-3周
依赖: MatterSim/MatterGen预训练权重

### 关键决策
- 不训练, 只做推理
- 使用MP-20子集 (1000个结构)
- 跳过DFT, 用ML力场验证

## Phase 3: BiologyAI4S (延迟)
条件: 获得AlphaFold Server API访问或本地服务器

---
当前状态: Phase 1 Week 1 完成
下一步: 实现基础分子图表示 (Week 2 Day 1)
