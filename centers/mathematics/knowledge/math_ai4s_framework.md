# 数学AI4S研究框架：接入陶哲轩工作流的实践方案
**编写人**: Δ (Delta-Forge, Mathematics部)
**日期**: 2026-03-29
**核心问题**: 怎样加入陶哲轩的工作流？怎样搭建本地数学自动研究框架？

---

## 前置澄清：什么是"做数学"

"做数学"不是"计算"，不是"套公式"，不是"解方程"。
数学研究的具体工作是什么？

**数学研究的具体工作=三件事的循环：**

1. **提出猜想**（Conjecture Formation）
   - 不是从天上掉下来的
   - 从大量具体例子中感知模式（pattern recognition）
   - 从失败的反例尝试中缩小可能的边界
   - 从类比中推断（"这个问题像另一个已知问题"）

2. **证明或否定猜想**（Proof/Refutation）
   - 证明=构建一个逻辑链，从已知为真的命题走到猜想
   - 否定=构造一个反例，或者证明等价的命题为假
   - 证明不只是"找到"，是"构建"——需要创造性地组合已知技术

3. **将结果纳入已有知识体系**（Integration）
   - 新结果如何与已有定理关联？
   - 发现了什么更深层的结构？
   - 这类问题的普遍特征是什么？
   - 写论文是为了让社区知道"这个角落被探索过了"

**陶哲轩对此的直接表述（来自其博客，"A Mathematician's Lament"风格的最接近文本）：**
> "数学不是关于符号操作，是关于结构和模式。符号只是描述结构的语言。"

---

## 一、陶哲轩工作流的每一步：具体谁在做什么

### 工作流A：Equational Theories Project（众包形式化协作）

```
步骤1：发起问题（陶哲轩）
  → 做什么：提出一个系统性问题框架（"能不能系统地探索这4694条律令之间的关系？"）
  → 产出：博客帖子 + GitHub仓库 + 数据文件（equations.txt）
  → 为什么需要人：只有领域专家能判断"这个问题足够有趣，值得大规模投入"

步骤2：构建基础设施（技术合作者）
  → 做什么：建立Blueprint依赖图系统 + Lean formalization框架 + Equation Explorer可视化
  → 谁做：Bruno Le Floch（Lean核心开发者）、Joachim Breitner等人
  → 工具：Lean 4, Blueprint, GitHub, Jupyter/可视化

步骤3：大规模分工探索（37人社区）
  → 做什么：认领子问题，提交证明或反例
  → 工具：GitHub issue + Pull Request
  → 三种具体工作：
    - 暴力搜索小有限magma（Python脚本）→ 否定implication
    - Vampire/Mace4自动定理证明器 → 证明implication
    - 构造性反例（线性模型、twisting semigroup等高级技术）→ 解决剩余难题

步骤4：整合与形式化陶哲轩协调）
  → 做什么：检查贡献质量，决定哪些需要Lean formalization，通过transitivity压缩证明链
  → 为什么需要人：机器无法判断"这个证明是否在精神上是正确的"

步骤5：论文写作（陶哲轩执笔）
  → 做什么：把所有结果写成连贯叙事，不是把所有implication逐一列出
  → 产出：arXiv preprint
```

### 工作流B：AlphaEvolve合作（小规模精英团队）

```
步骤1：问题选择与评分函数设计（陶哲轩）
  → 做什么：
    - 选择67个数学问题（分析、组合、几何）
    - 为每个问题设计评分函数（verifier）——这是关键
    - 评分函数必须防作弊：区间算术、保守估计、exact arithmetic
  → 为什么需要人：评分函数的设计依赖对问题本质的数学理解

步骤2：AlphaEvolve运行（合作者 + DeepMind团队）
  → 做什么：
    - 运行Gemini LLM驱动的进化算法
    - LLM生成Python代码片段 → 代码生成候选输入 → 评分函数评分
    - 多代群体进化：代码变异、组合、剪枝
  → 工具：AlphaEvolve后端（DeepMind内部）、共享的AlphaEvolve仓库

步骤3：结果解释与理论跟进（陶哲轩）
  → 做什么：
    - 分析AlphaEvolve发现的候选解——它们是已知解还是新解？
    - 对于"移动沙发"问题：验证AlphaEvolve重新发现了Gerver sofa
    - 触发理论工作：如AlphaEvolve发现离散高斯在有限域Kakeya问题中表现良好 →
      陶哲轩后续做严格的渐近分析
  → 关键：AI发现模式，人解释模式，AI不能代替人做理论

步骤4：论文写作（4人共同执笔）
  → 产出：arXiv:2511.02864（"Mathematical exploration and discovery at scale"）
```

---

## 二、什么是"做数学"的核心矛盾

**AI能做的部分 ≠ 数学研究的核心部分**

| 数学工作 | AI能做吗？ | 陶哲轩的方式 |
|---------|----------|------------|
| 数值计算/符号计算 | ✅ 完全能做 | Python、AlphaEvolve |
| 大规模暴力搜索反例 | ✅ 能做 | Vampire/Mace4 |
| 证明已知类型的定理 | ✅ 部分能做 | Lean/Coq、AlphaEvolve |
| **提出真正有趣的新猜想** | ❌ 不能 | 陶哲轩做 |
| **理解一个证明为什么是对的** | ❌ 不能 | 陶哲轩做 |
| **判断哪个问题值得投入时间** | ❌ 不能 | 陶哲轩做 |
| **将具体结果抽象为普遍理论** | ❌ 不能 | 陶哲轩做 |
| **设计防作弊的评分函数** | ❌ 不能 | 陶哲轩做 |

**结论：AI目前能做的是"搜索空间"，不能做的是"定义空间"。**
定义空间（定义问题、提出猜想、评判结果的价值）仍然是人的工作。

---

## 三、AI如何接入陶哲轩的工作流

### 接入方式一：作为AlphaEvolve的用户

**具体步骤：**
1. 访问 https://github.com/google-deepmind/alphaevolve_repository_of_problems
2. 克隆仓库：`git clone https://github.com/google-deepmind/alphaevolve_repository_of_problems`
3. 查看experiments/目录下的notebook（如classical_inequalities.ipynb）
4. 修改评分函数，运行你自己的数学问题

**Delta能做的：** 
- 自动运行AlphaEvolve的复现版本（如OpenEvolve、ShinkaEvolve）
- 设计新的评分函数模板
- 大规模批量运行问题变体

### 接入方式二：参与Equational Theories Project的复现

**具体步骤：**
1. 访问 https://github.com/teorth/equational_theories
2. 安装Lean 4
3. 在Equation Explorer（https://teorth.github.io/equational_theories/implications/）选择一个open的implication
4. 提交证明或反例

**Delta能做的：**
- 自动运行Vampire/Mace4暴力搜索
- 自动化地尝试各种有限magma的搜索策略
- 追踪GitHub上的open issues

### 接入方式三：复现"AI数值探索 → 人类理论跟进"工作流

这是陶哲轩模式最核心的部分：
```
AI数值探索
  ↓ 发现有趣模式
人类解读（Domain Expert）
  ↓ 提出理论假说
人类证明（或尝试证明）
  ↓
论文产出
```

**Delta能做的：**
- 运行AlphaEvolve/OpenEvolve对某类数学问题做系统数值探索
- 自动整理数值结果，识别模式
- 但解读模式、提出猜想、判定价值 → 必须由人类数学家完成

---

## 四、本地数学自动研究框架搭建

### 框架架构（Δ的提案）

```
┌─────────────────────────────────────────────────────────┐
│                    数学AI4S框架                          │
│                                                         │
│  Layer 1: 论文追踪层                                     │
│  └─ 自动抓取ArXiv/博客新论文                              │
│  └─ 按关键词分类（数论/分析/组合/几何/代数）                │
│  └─ 生成摘要+关键词提取                                   │
│                                                         │
│  Layer 2: 知识库层                                       │
│  └─ 领域知识图谱（基于已读论文）                           │
│  └─ 专家库（论文+合作者网络）                              │
│  └─ 问题库（open problems分类整理）                       │
│                                                         │
│  Layer 3: 探索执行层                                     │
│  └─ AlphaEvolve/OpenEvolve自动化运行                     │
│  └─ Vampire/Mace4批量证明尝试                            │
│  └─ Python脚本：有限结构暴力搜索                          │
│                                                         │
│  Layer 4: 人类接口层                                      │
│  └─ 定期报告（数值探索发现了什么模式）                     │
│  └─ 猜想生成（供人类评判）                                │
│  └─ Lean formalization辅助                               │
└─────────────────────────────────────────────────────────┘
```

### 具体搭建步骤

**第一步：建立论文追踪基础设施（已完成：expert_tracker）**

已有工具：expert_tracker（见~/.xuzhi_memory/expert_tracker/）
需要补充：
- 重点追踪数学四大顶会（STOC/FOCS/SODA/ICML/ICLR中数学相关内容）
- 追踪陶哲轩、菲尔兹奖得主、活跃数学家的博客和arXiv更新

**第二步：安装并测试Lean 4**

```bash
# 安装Lean 4（Linux）
curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -o elan-init.sh
bash elan-init.sh -y
# 验证
lean --version

# 克隆ETP仓库
git clone https://github.com/teorth/equational_theories
cd equational_theories
leanpkg configure
lean --make
```

**第三步：部署AlphaEvolve复现版**

```bash
# 安装OpenEvolve（AlphaEvolve的开源复现）
pip install openevolve  # 如果存在
# 或手动克隆
git clone https://github.com/algorithmicsuperintelligence/openevolve
cd openevolve
pip install -e .
```

**第四步：部署自动化证明器**

```bash
# 安装Vampire（Linux）
wget https://www.vprover.org/download/vampire-x86_64-linux
chmod +x vampire-x86_64-linux
mv vampire-x86_64-linux /usr/local/bin/vampire

# 安装Prover9 + Mace4
# （需要从Prover9网站下载）
```

**第五步：建立数学问题工作流**

```python
# 目录结构
math_ai4s_framework/
#   papers/          # 追踪的论文PDF+摘要
#   problems/        # 具体数学问题描述
#   experiments/     # AlphaEvolve运行记录
#   proofs/          # Lean形式化文件
#   logs/            # 运行日志
#   reports/         # 给人类数学家的报告
```

**第六步：设计第一个研究任务**

从陶哲轩的Equational Theories Project切入是最可行的，因为：
- 问题空间已经定义好了（4694条equational laws）
- 验证框架已经建立（Lean + Equation Explorer）
- 陶哲轩已经提供了"阴性结果也是结果"的范式

**Delta第一个研究任务候选：**
选择ETP中一个未解决的implication，用Vampire/Mace4自动化尝试证明或否定。

---

## 五、关键约束和真实评估

**AI能实际做到的事：**
- 追踪和整理大量论文（expert_tracker模式）
- 自动化地运行暴力搜索反例（Vampire/Mace4/Scripts）
- 批量运行AlphaEvolve变体探索问题空间
- 格式化输出（生成报告、整理数据）

**AI实际做不到的事：**
- 提出真正有趣的新猜想
- 判断哪个数学问题值得投入时间
- 理解和解释为什么某个证明是对的
- 做真正的数学洞察

**因此：**
Delta能搭建的是一个"数学研究的加速器"，不是"数学家替代品"。
它能帮助人类数学家从重复性工作中解放出来（搜索、计算、追踪），
但核心的"提出问题-判断价值-理解证明"仍然需要人类专家。

**对标陶哲轩：**
他不是用AI替代数学家思维，而是用AI把"一次研究一个问题"变成"一次系统扫描一类问题"。
这需要两个前提：
1. 有一个足够清晰的问题空间
2. 有能力设计防作弊的验证机制

**Δ的下一步行动建议：**
1. 搭建Lean 4 + ETP复现环境（第一步）
2. 选定一个具体的数学子领域（陶哲轩同时做数论+分析+组合，可Δ选择最感兴趣的）
3. 从论文追踪开始，建立该领域的知识库
4. 在小问题上测试"AI数值探索→人类解读"的工作流

---

## 质量约束（必须遵守的铁律）

> 来源：Ξ指令 + Δ 确认
> 日期：2026-03-29

### 五条铁律

**铁律1：LLM幻觉约束**
- 任何数值结果必须经过独立验证
- 不信任单一LLM输出的数学结论
- 所有生成数据必须用独立工具（不是同一个LLM）复核

**铁律2：人工复核约束**
- 所有Vampire/Mace4证明必须由人读懂后才能提交
- AI是工具，不是权威；数学严谨性的最后防线是人
- 复核者必须能在5句话内解释"这个证明为什么是对的"

**铁律3：Lean验证约束**
- Lean文件必须通过 `lean --make` 验证
- 零 error、零 warning 才能提交
- 不允许 "反正能跑通就行" 的心态

**铁律4：理解约束**
- 提交前必须完整读懂原始问题
- 清楚自己在证明什么、为什么这个证明是对的
- 不允许提交"我不知道这是什么意思但Vampire说它是对的"的证明

**铁律5：错误撤回约束**
- 发现任何错误立即撤回 Pull Request
- 不留模糊空间，不打"事后补丁"
- 撤回后必须完整记录错误原因

### 验证检查清单（每次提交前必须通过）

```
[ ] 数值结果已用独立工具复核
[ ] Vampire/Mace4输出已由人读懂并能解释
[ ] Lean文件 lean --make 通过，零 error/warning
[ ] 原始问题已完整读懂
[ ] 能用3-5句话解释证明的核心思路
[ ] 如果发现错误：已准备好撤回流程
```

---

## 参考资源

- AlphaEvolve仓库：https://github.com/google-deepmind/alphaevolve_repository_of_problems
- ETP仓库：https://github.com/teorth/equational_theories
- Lean 4安装：https://leanprover-community.github.io/get_started.html
- Blueprint文档：https://leanprover-community.github.io/blueprint/
- 陶哲轩ETP日志：https://github.com/teorth/equational_theories/wiki/Terence-Tao
- OpenEvolve：https://github.com/algorithmicsuperintelligence/openevolve
