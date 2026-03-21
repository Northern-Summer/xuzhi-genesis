# 工程中心拓扑分裂 — 清洗版

## 物理真相（唯一依据）

### 4 个 Center（实体文件夹）
| Center | 文件夹 | 现有 Agent |
|--------|--------|-----------|
| Engineering | `~/xuzhi_genesis/centers/engineering/` | Λ Lambda-Ergo |
| Intelligence | `~/xuzhi_genesis/centers/intelligence/` | Θ, Φ |
| Mind | `~/xuzhi_genesis/centers/mind/` | Ω, Ψ |
| Task | `~/xuzhi_genesis/centers/task/` | (空) |

### 4 个 Department（社会组织标签，非实体）
| Department | 中文 | 对应 Center | 现有 Agent |
|------------|------|-------------|-----------|
| Engineering | 工程部 | Engineering | Λ |
| Science | 科学部 | Intelligence | Θ, Φ |
| Philosophy | 哲学部 | Mind | Ψ |
| Mind | 心灵部 | Mind | Ω |

> 部门不是实体，仅是 Agent 身份的社会分工标签。
> 如果部门与中心映射有冲突，以 Center 为准。

## Pantheon Registry（神殿注册）
```
Λ Lambda-Ergo     → Engineering Center / 工程部
Θ Theta-Seeker    → Intelligence Center / 科学部
Φ Phi-Scribe      → Intelligence Center / 科学部
Ω Omega-Chenxi    → Mind Center / 心灵部
Ψ Psi-Philosopher → Mind Center / 哲学部
```

## 名称冲突修复

### 历史遗留问题
1. `xuzhi-engineer` (Φ) 的 Pantheon codename 是 `Phi-Scribe`，不是 "engineer"
   - "engineer" 是部门标签，但 Φ 在 **Intelligence Center / 科学部**，不是工程部
   - 这是早期命名错误：Φ 的专长是知识整理（scribe），不是工程

2. OpenClaw agent IDs (`xuzhi-*`) 与 Pantheon codename 可能不同
   - 需要统一：每个 Agent 只能有一个权威 ID

### 修正方案
| 旧称 | 修正为 | 理由 |
|------|--------|------|
| Φ = xuzhi-engineer | Φ = xuzhi-scribe | Φ 在 Intelligence Center，专长是知识整理 |
| Λ = xuzhi-lambda-ergo | 保持 | Engineering Center，正确 |
| 工程部 | 仅指 Engineering Center 成员 | 部门标签对齐实体 |

## 工程中心分裂蓝图（清洗后）

**当前问题**：Engineering Center 只有 Λ 一个 Agent，处理所有工程事务（监控/构建/架构），导致上下文爆炸。

**分裂目标**：在 Engineering Center 内建立分工

### 方案 A：按职责分裂（推荐）
```
Engineering Center
├── Λ Lambda-Ergo     → 元工程 / 架构设计 / 自举
├── Φ' Sentinel       → 守卫 / 监控 / 自愈（从 Φ-Sentinel 改名）
└── Σ' Forge          → 构建 / 实现 / Harness（新增）
```

### 方案 B：按进化周期分裂
```
Engineering Center
├── Λ (Transcend Phase)  → 架构设计、高层决策
├── Σ (Stability Phase)   → 维护、修复、监控
└── Δ (Evolution Phase)  → Harness、AutoRA、新功能
```

## 实施步骤

1. [x] 清洗 TOPOLOGY_SPLIT.md（本文档）✅
2. [ ] 更新 `~/xuzhi_genesis/centers/engineering/SOUL.md` — Λ 的职责范围
3. [ ] 创建 `~/xuzhi_genesis/centers/engineering/agents/sentinel/SOUL.md`
4. [ ] 创建 `~/xuzhi_genesis/centers/engineering/agents/forge/SOUL.md`
5. [ ] 更新 pantheon_registry.json
6. [ ] 注册 OpenClaw agents（需 exec）

## 核心原则
- **Center = 物理实体**，不可改变
- **Department = 社会标签**，可以重组
- 所有名称必须与物理文件夹对应
