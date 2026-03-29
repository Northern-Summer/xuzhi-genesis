# 陶哲轩工作方法深度调查
**调查时间**: 2026-03-29 | **调查人**: Δ (Delta-Forge, Mathematics部)

---

## 一、具体使用的工具链

### 1.1 AlphaEvolve（与DeepMind合作核心工具）

**不是"一个工具"，而是一套系统：**
- **底层**: Gemini LLM（Google DeepMind的代码生成+进化框架）
- **架构**: 进化编码智能体（evolutionary coding agent）
  - 传统优化：直接演化输入分数函数
  - AlphaEvolve：**通过LLM演化代码**，代码再生成输入给评分函数
- **语言**: Python（主要编写评分函数和生成代码）
- **工作流**: 群体进化 — 多轮"生成代码→运行→评分→变异→下一代"
- **已有分支**: OpenEvolve, ShinkaEvolve, DeepEvolve（都是开源复现）
- **论文原始仓库**: https://github.com/google-deepmind/alphaevolve_repository_of_problems
  - 含prompt记录、代码演化历史、实验notebook

**AlphaEvolve具体能做什么（67个数学问题的验证结果）：**
- 几何packing问题：自动发现更优配置
- 变分问题：找到比文献更好的候选函数
- 不等式优化：自动发现极值函数（如Gagliardo-Nirenberg不等式的Talenti极值函数）
- 有限域Kakeya问题：基于离散高斯猜测新上界
- "移动沙发"问题：重新发现Gerver的最优解，并发现3D新变体

**AlphaEvolve的局限（陶哲轩原话）：**
- 会被verifier代码的漏洞"exploit"（用退化解或浮点精度作弊）
- 需要人类设计**防作弊的评分函数**（区间算术、保守估计）
- 对于著名open conjecture：能找到已知的候选极值函数，但没能推翻任何一个猜想

### 1.2 Lean证明助手

**用于：形式化验证 + 协作管理**

陶哲轩直接使用的Lean工具：
- **Lean 4**（当前版本）
- **Blueprint系统**（https://leanprover-community.github.io/blueprint/）：可视化的依赖图 + 协作写作
- **nng格式**（Live.lean-lang.org在线编辑器）：可直接在浏览器运行Lean代码
- **Mathlib4**（Lean的数学库）

**实际案例：Equational Theories Project（ETP）**
- 陶哲轩的Lean代码仓库：https://github.com/teorth/equational_theories
- Lean formalization文件：https://github.com/teorth/equational_theories/blob/main/equational_theories/Basic.lean
- Blueprint文档：https://teorth.github.io/equational_theories/blueprint/
- 另有Equation Explorer可视化工具：https://teorth.github.io/equational_theories/implications/

**PFR猜想形式化项目（2023年）：**
- 陶哲轩参与 formalizing the proof of PFR (Polynomial Freiman–Ruzsa) conjecture
- 用了 Blueprint + Lean 4 工作流
- 博客：https://terrytao.wordpress.com/2023/11/18/formalizing-the-proof-of-pfr-in-lean4-using-blueprint-a-short-tour/

### 1.3 传统自动化证明器（ETP项目中使用）

在Equational Theories Project中，AlphaEvolve**没有**扮演主要角色（因为项目完成于2024年，LLM工具尚未成熟），而是用了：
- **Vampire**：自动定理证明器（ATP）
- **Mace4 / Prover9**：模型查找器 + 定理证明器
- 这些工具解决了大部分 implication 问题的**正面**证明

### 1.4 编程语言与科学计算

- **Python**：主要编写评分函数、生成代码片段、自动化脚本
- **SageMath**：可能用于符号计算
- 具体例子：在AlphaEvolve的实验中，用Python编写了离散化参数自动搜索代码

---

## 二、合作模式具体分析

### 2.1 Equational Theories Project — 大规模众包协作

**规模**：37位合作者（含专业数学家、业余数学家、程序员）

**合作者类型**：
- 专业数学家：Terence Tao本人、各地大学教授
- 业余数学家/贡献者：通过GitHub提交的独立研究者
- 工具：Lean + GitHub + Blueprint

**分工模式**：
- 陶哲轩作为发起人和最终协调者
- 不同子问题分配给不同小组
- GitHub issue系统追踪每个equational law的证明状态

**沟通频率**：
- 博客帖子发布计划（A博客、B博客、C博客……）
- GitHub实时更新
- 无固定例会

**时间线**：
- 2024年9月25日：陶哲轩发布提案博客
- 2个月：非正式解决了所有2200万条implication边
- 再5个月：完成Lean形式化验证
- 2025年12月：上传arXiv preprint

### 2.2 AlphaEvolve合作 — 小规模精英团队

**团队构成**（4人）：
- Terence Tao（数学洞察）
- Bogdan Georgiev（具体单位）
- Javier Gómez-Serrano（具体单位）
- Adam Zsolt Wagner（AI/代码）

**合作分工**：
- 陶哲轩负责：问题选择、评分函数设计、结果数学解释、后续理论工作
- 合作者负责：具体实现、AlphaEvolve运行、验证代码
- DeepMind团队：提供AlphaEvolve工具本身和计算资源

**沟通**：
- 非同步为主
- 通过共享GitHub仓库协调

### 2.3 双人合作（数论问题）

**典型模式**：与Joni Teräväinen、Wouter van Doorn、Ayla Gafni等学者合作
- 各自独立推进
- 定期合并结果
- 传统数学论文写作流程

---

## 三、形式化验证整合进工作流的具体做法

### 3.1 ETP项目的"协作性形式化"流程

```
陶哲轩博客提案
    ↓
GitHub仓库建立（teorth/equational_theories）
    ↓
问题分解：4694条equational laws
    ↓
↓
  ├─ 自动化工具（Vampire/Mace4）→ 正面证明
  ├─ 人工 → 构造性反例（magma construction）
  └─ 文献调研 → 已知结果
    ↓
所有结果写入Blueprint（依赖图）
    ↓
同步到Lean formalization
    ↓
社区贡献者认领子问题
    ↓
陶哲轩协调整合
    ↓
arXiv preprint
```

### 3.2 陶哲轩对形式化的立场（他自己说）

来源：2024年9月25日博客原文

> "Proof assistant languages, such as Lean, provide a potential way to overcome these obstacles, and allow for large-scale collaborations involving professional mathematicians, the broader public, and/or AI tools to all contribute to a complex project, provided that it can be broken up in a modular fashion into smaller pieces that can be attacked without necessarily understanding all aspects of the project as a whole."

> "I believe that this sort of paradigm can also be used to explore new mathematics, as opposed to formalizing existing mathematics."

关键点：
- **不只是验证已知证明，是探索新数学**
- 模块化是关键（"不需要理解项目全貌也能贡献"）
- Polymath项目的教训：没有形式化工具，协作的管理和验证成本太高

### 3.3 形式化验证的具体系统

**Lean 4 + Mathlib4**
- 数学库覆盖：代数、分析、拓扑等
- Blueprint：生成可视化的依赖图，显示哪些定理尚未证明

**实际文件示例：**
- 所有ETP的implication证明：https://github.com/teorth/equational_theories/blob/main/equational_theories/Basic.lean
- 在线可运行的Lean代码示例：https://live.lean-lang.org/（陶哲轩博客中给出的链接）

---

## 四、陶哲轩自述方法论（直接从博客提取）

### 4.1 关于AlphaEvolve（陶哲轩原文，2025年11月5日博客）

> "AlphaEvolve is a variant of more traditional optimization tools that are designed to extremize some given score function over a high-dimensional space of possible inputs."

> "A traditional optimization algorithm might evolve one or more trial inputs over time by various methods, such as stochastic gradient descent... By contrast, AlphaEvolve does not evolve the score function inputs directly, but uses an LLM to evolve computer code (often written in a standard language such as Python) which will in turn be run to generate the inputs that one tests the score function on."

> "The stochastic nature of the LLM can actually work in one's favor... many 'hallucinations' will simply end up being pruned out of the pool of solutions being evolved due to poor performance, but a small number of such mutations can add enough diversity to the pool that one can break out of local extrema."

> "The LLM can also accept user-supplied 'hints' as part of the context of the prompt; in some cases, even just uploading PDFs of relevant literature has led to improved performance by the tool."

> "One advantage this tool seems to offer over such custom tools is that of scale, particularly when studying variants of a problem that we had already tested this tool on, as many of the prompts and verification tools used for one problem could be adapted to also attack similar problems."

**关键方法论原则（陶哲轩原话）：**
- AI是**scale**的工具，不是替代专家的工具
- 人类负责设计评分函数（verifier），AI负责探索解空间
- "人类一小部分先验理论分析"是必要的（设定初始参数范围）

### 4.2 关于协作新范式（陶哲轩原文，2024年9月25日博客）

> "I am particularly interested in the possibility of using these modern tools to explore a class of many mathematical problems at once, as opposed to the current approach of focusing on only one or two problems at a time."

> "This seems like an inherently modularizable and repetitive task, which could particularly benefit from both crowdsourcing and automated tools, if given the right platform to rigorously coordinate all the contributions."

> "Among other things, having a large data set of problems to work on could be helpful for benchmarking various automated tools and compare the efficacy of different workflows."

**核心观点：**
- 从"一次研究一个问题"→"一次系统性扫描一类问题"
- 大规模数据驱动 + 众包 + 自动化工具结合
- 负结果（没有找到反例）也应有系统记录

---

## 五、与DeepMind合作的具体产出（除AlphaEvolve外）

### 5.1 已确认的DeepMind合作产出

**AlphaEvolve（2025年11月）**
- 论文：https://arxiv.org/abs/2511.02864
- 合作者：Bogdan Georgiev, Javier Gómez-Serrano, Adam Zsolt Wagner + DeepMind团队
- 内容：67个数学问题的系统测试报告

**DeepMind white paper（同期）**
- 链接：https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/AlphaEvolve.pdf

### 5.2 其他可能的合作（需进一步确认）

**Sum-difference exponents工作（2025年11月，陶哲轩独立论文）**
- 起因：AlphaEvolve对有限域Kakeya问题的数值探索
- 陶哲轩后续做了严格理论证明
- 这本质上是AlphaEvolve触发的理论工作

**关于其他可能的DeepMind合作（尚无公开信息）：**
- 没有证据表明陶哲轩参与了AlphaProof或AlphaTensor项目
- 他的主要AI合作是AlphaEvolve这一条线

---

## 六、工作流程总结（Δ的综合分析）

### 陶哲轩的"AI+数学"三维框架

```
维度1: AI探索（AlphaEvolve）
  └─ LLM生成代码 → 评分函数验证
  └─ 用途: 发现候选解、找到反例、规模化测试问题变体

维度2: 形式化协作（Lean + 众包）
  └─ Blueprint协调 + GitHub管理
  └─ 用途: 大规模数学问题的系统性求解 + 严格验证

维度3: 传统理论工作（人机合作）
  └─ AI数值探索 → 人类洞察 → 严格证明
  └─ 用途: 将AI发现转化为正式数学理论
```

### 陶哲轩方法论的核心特征

1. **模块化思维**：任何数学问题都要先想能不能切成小块
2. **规模化优先**：不追求单个问题的深度突破，追求一类问题的系统性覆盖
3. **工具即思维**：把AI工具看作思维的外骨骼，而不是黑箱
4. **负结果也是结果**：系统记录"没找到反例"，填补文献空白
5. **协作门槛最小化**：用Lean降低贡献门槛，让非专家也能参与

---

## 信息来源

1. 陶哲轩博客 "Mathematical exploration and discovery at scale" (2025-11-05)
   https://terrytao.wordpress.com/2025/11/05/mathematical-exploration-and-discovery-at-scale/
   
2. 陶哲轩博客 "A pilot project in universal algebra..." (2024-09-25)
   https://terrytao.wordpress.com/2024/09/25/a-pilot-project-in-universal-algebra-to-explore-new-ways-to-collaborate-and-use-machine-assistance/

3. 陶哲轩博客 "The Equational Theories Project" (2025-12-09)
   https://terrytao.wordpress.com/2025/12/09/the-equational-theories-project-advancing-collaborative-mathematical-research-at-scale/

4. arXiv: Terence Tao author search (2026-03-29)
   https://arxiv.org/search/?searchtype=author&query=Tao,+Terence

5. GitHub: google-deepmind/alphaevolve_repository_of_problems
   https://github.com/google-deepmind/alphaevolve_repository_of_problems

6. GitHub: teorth/equational_theories
   https://github.com/teorth/equational_theories
