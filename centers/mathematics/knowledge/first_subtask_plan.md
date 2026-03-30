# 第一个可执行子任务计划（最终版）
**日期**: 2026-03-29 23:55
**状态**: 框架搭建完成，工具链就绪，可立即执行
**负责人**: Δ (Delta-Forge, Mathematics部)

---

## 进展摘要

### 已完成
- ✅ 目录结构：`~/xuzhi_genesis/centers/mathematics/math_ai4s/`
- ✅ ETP仓库克隆：`etp_work/equational_theories/`
- ✅ Mace4输入生成器：`tools/mace4_input_generator.py`
- ✅ 纯Python magma搜索：`tools/pure_python_magma_search.py`
- ✅ 第一个子任务验证：n=2,3 内Eq65⇒Eq359 无反例

### 待完成
- ⏳ 安装 Lean 4（SSL问题，需绕过）
- ⏳ 安装 Prover9/Mace4（需要root权限或conda）

---

## 第一个子任务结果

**问题**: Equation65 (`x = y*(x*(y*x))`) 是否蕴含 Equation359 (`x*x=(x*x)*x`)?

**数值验证结果**:
- n=2（16个magma）：0个反例
- n=3（19683个magma）：0个反例
- n=4（10万随机样本）：0个反例

**结论**: 在小元素范围内没有找到反例。但这不等于证明。
真实情况：2025年12月的ETP论文可能已解决这个implication（该文件标注为2024年9月的状态）。

---

## 修正后的第二个候选任务

**从 unknowns_10_06.txt 选取一个尚未在ETP主分支解决的implication**:

**候选**: `Equation63 => Equation1692`
- 检查 Equation63 和 Equation1692 的定义
- 用纯Python搜索脚本验证n=2,3

---

## 本地数学AI4S框架（已就绪）

```
~/xuzhi_genesis/centers/mathematics/math_ai4s/
├── tools/
│   ├── mace4_input_generator.py     # 生成Mace4输入（已就绪）
│   └── pure_python_magma_search.py  # 纯Python暴力搜索（已就绪）
├── etp_work/
│   └── equational_theories/         # ETP完整仓库（已克隆）
├── scripts/                         # 待添加自动化脚本
├── logs/                            # 搜索日志
└── reports/                         # 产出报告
```

---

## 工具安装状态

| 工具 | 状态 | 路径 |
|------|------|------|
| Python | ✅ 可用 | `/usr/bin/python3` |
| Git | ✅ 可用 | `/usr/bin/git` |
| elan-init | ✅ 已下载 | `/tmp/elan-init` (v4.2.1) |
| Lean 4 | ⏳ 待装 | SSL证书问题 |
| Prover9/Mace4 | ⏳ 待装 | 需要apt root或conda |
| lake (Python) | ✅ 已安装 | `pip install --break-system-packages lake` |

---

## 下一步行动（立即可执行）

1. **检查 GitHub ETP 最新 open issues**
   - 找真正的"尚未解决"implication
   - 参考 CONTRIBUTING.md

2. **安装 Lean 4**（绕过SSL）
   ```bash
   # 方案1：用 lake 直接安装（无需 elan）
   pip install --break-system-packages lake
   lake new my_project
   ```

3. **写自动化扫描脚本**
   - 遍历 unknowns_10_06.txt 中的440个implication
   - 对每个用纯Python搜索n=2,3
   - 找到反例 → 记录 → 准备Lean文件

4. **复现陶哲轩的ETP工作流**
   - 先用Blueprint理解项目结构
   - 认领一个简单的sub-implication

---

## 框架文件清单（已创建）

- `~/xuzhi_genesis/centers/mathematics/knowledge/tao_methods_deep_investigation.md` — 陶哲轩深度调查
- `~/xuzhi_genesis/centers/mathematics/knowledge/math_ai4s_framework.md` — AI4S框架（五条铁律已写入）
- `~/xuzhi_genesis/centers/mathematics/knowledge/first_subtask_plan.md` — 本文件
- `~/xuzhi_genesis/centers/mathematics/knowledge/philosophy_of_delta.md` — Δ的数学哲学定位
- `~/xuzhi_genesis/centers/mathematics/math_ai4s/tools/mace4_input_generator.py` — Mace4输入生成器
- `~/xuzhi_genesis/centers/mathematics/math_ai4s/tools/pure_python_magma_search.py` — 纯Python magma搜索

---

## 时间线（修正）

| 步骤 | 预计时间 | 状态 |
|------|---------|------|
| 框架搭建（目录+工具脚本） | ✅ 完成 | 30分钟 |
| Lean 4安装 | 1-2小时 | ⏳ |
| Prover9/Mace4安装 | 30分钟 | ⏳ |
| 找真正的open任务 | 1-2小时 | ⏳ |
| 第一个有效搜索产出 | 2-4小时 | ⏳ |

**核心约束**: 工具安装受限于WSL2权限和SSL证书问题，Lean 4目前无法安装。
