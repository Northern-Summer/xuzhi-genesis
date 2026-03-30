# MatterGen 核心架构解析 | Γ
> 对标对象：Microsoft Research | 来源：github.com/microsoft/mattergen
> 解析日期：2026-03-30

---

## 一、系统定位

**MatterGen** = 无机材料生成模型，基于**扩散模型**，支持：
- 无条件生成（unconditional）
- 属性条件生成（property-conditioned）
- 多属性联合条件生成（multi-property）

**核心能力**：给定属性约束 → 生成稳定材料结构

---

## 二、核心架构（必须Copy）

### 2.1 整体架构

```
MatterGen
├── 扩散模型主干
│   ├── 输入：随机结构（原子位置 + 元素类型 + 晶格参数）
│   ├── 输出：稳定晶体结构
│   └── 去噪过程：逐步从噪声恢复结构
├── 属性嵌入模块（Property Embeddings）
│   ├── 连续值属性：band_gap, bulk_modulus, mag_density
│   ├── 离散属性：space_group, chemical_system
│   └── 适配器机制：Adapter微调
└── 评估管道
    ├── MatterSim ML力场快速评估
    └── DFT精确验证（推荐）
```

### 2.2 扩散模型设计

**创新点1：周期性几何处理**
- 专门处理晶体周期性边界条件
- 3D几何扩散架构（区别于分子扩散模型）

**创新点2：组合无序处理**
- 结构匹配算法区分：有序近似 vs 真实无序
- 支持部分占据（partial occupancy）

**创新点3：联合去噪**
- 同时去噪：原子位置 + 元素类型 + 晶格参数
- 确保生成结构的物理一致性

### 2.3 属性条件机制

**分类器无关引导（Classifier-Free Guidance）**
- 参数 γ（gamma）控制条件强度
- γ=0：无条件生成
- γ>0：条件生成，γ越大，条件 adherence 越强

**多属性联合**
- 支持同时条件化多个属性
- 示例：{energy_above_hull: 0.05, chemical_system: "Li-O"}

---

## 三、训练流程（必须Copy）

### 3.1 数据

| 数据集 | 规模 | 用途 |
|--------|------|------|
| MP-20 | 45k | 基础训练 |
| Alex-MP-20 | 608k | 大规模训练 |
| Alexandria | 扩展数据 | 增强泛化 |

**数据筛选标准**：
- 单胞原子数 ≤ 20
- 能量凸包上方 < 0.1 eV/atom（热力学稳定）

### 3.2 训练策略

**阶段1：基础模型训练**
```bash
mattergen-train data_module=alex_mp_20 ~trainer.logger trainer.accumulate_grad_batches=4
```
- 目标：val_loss ≈ 0.4（360 epochs，约80k steps）
- 梯度累积：batch_size=512需要4步累积

**阶段2：属性微调**
```bash
mattergen-finetune adapter.pretrained_name=mattergen_base data_module=mp_20 +lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.dft_mag_density=dft_mag_density ~trainer.logger data_module.properties=["dft_mag_density"]
```
- Adapter机制：只微调属性嵌入，冻结主干
- 支持多属性联合微调

---

## 四、评估体系（必须Copy）

### 4.1 核心指标 S.U.N.

| 指标 | 定义 | MatterGen结果 |
|------|------|---------------|
| **S**table | 结构弛豫后稳定 | 74.41% |
| **U**nique | 去重后唯一结构 | 100% |
| **N**ovel | 不在训练/参考集中 | 61.96% |
| **S.U.N.** | 三者交集 | **38.57%** |

### 4.2 对比基线

| 模型 | S.U.N. | RMSD | Stable | Unique | Novel |
|------|--------|------|--------|--------|-------|
| **MatterGen** | **38.57%** | **0.021** | 74.41% | 100% | 61.96% |
| DiffCSP | 33.27% | 0.104 | 63.33% | 99.90% | 66.94% |
| CDVAE | 13.99% | 0.359 | 19.31% | 100% | 92.00% |

### 4.3 评估流程

**快速评估（MatterSim）**
```bash
mattergen-evaluate --structures_path=$RESULTS_PATH --relax=True --structure_matcher='disordered'
```

**精确验证（DFT）**
- 使用VASP/Quantum ESPRESSO计算形成能
- 能量校正方案：MP2020或TRI2024

---

## 五、关键创新（必须Copy）

### 5.1 生成优于筛选

**传统**：数据库 → 筛选 → 候选（受限于已知库）
**MatterGen**：约束 → 生成 → 验证（探索空间无限）

### 5.2 实验验证闭环

```
AI生成 → 计算验证 → 实验合成 → 测量验证 → 反馈优化
   ↑                                              ↓
   └──────────────────────────────────────────────┘
```

**论文实验案例**：TaCr₂O₆
- AI生成 → 合成 → XPS/XRD验证 → 纳米压痕测量

### 5.3 开放科学

- **开源**：github.com/microsoft/mattergen
- **开放数据**：Alex-MP-20, MP-20
- **模型权重**：Hugging Face托管

---

## 六、与Δ的MathAI4S对接点

| Δ组件 | MatterGen适配 | 对接方式 |
|-------|--------------|----------|
| **枚举搜索** | 化学系统枚举 | Δ生成候选化学式 → MatterGen生成结构 |
| **线性模型** | Vegard定律验证 | Δ验证固溶体线性近似 |
| **对称性分析** | 空间群约束 | Δ分析对称性 → MatterGen条件生成 |
| **Lean验证** | 物理约束形式化 | Δ形式化能量守恒/对称性约束 |

---

## 七、PhysicsAI4S设计草案

基于MatterGen最佳实践，设计PhysicsAI4S核心组件：

### 7.1 生成器（Generator）

```python
class PhysicsGenerator:
    """
    材料结构生成器（对标MatterGen）
    """
    def __init__(self):
        self.diffusion_model = DiffusionModel(
            periodic_boundary=True,  # 周期性处理
            joint_denoising=True     # 联合去噪
        )
        self.property_adapters = {}  # 属性适配器
    
    def generate(
        self,
        constraints: Dict[str, Any],
        guidance_factor: float = 2.0
    ) -> List[CrystalStructure]:
        """
        约束生成材料
        
        constraints示例：
        {
            "chemical_system": "Li-Mn-O",
            "space_group": "P6_3/mmc",
            "band_gap": ">2.0 eV",
            "bulk_modulus": ">150 GPa"
        }
        """
        pass
```

### 7.2 验证器（Validator）

```python
class PhysicsValidator:
    """
    多层验证（对标MatterGen评估管道）
    """
    def __init__(self):
        self.physics_checker = PhysicsChecker()      # 快速物理检查
        self.ml_relayer = MatterSimRelayer()         # ML力场弛豫
        self.dft_validator = DFTValidator()          # DFT精确验证
    
    def validate(self, structure: CrystalStructure) -> ValidationResult:
        """
        三级验证：
        1. 物理合理性（电荷平衡、键长范围）
        2. ML力场弛豫 + 稳定性判断
        3. DFT计算（能量、带隙、力学性质）
        """
        pass
```

### 7.3 数据管道

```python
class PhysicsDataPipeline:
    """
    数据管理（对标Alex-MP-20）
    """
    def __init__(self):
        self.sources = [
            "Materials Project",
            "Alexandria",
            "OQMD",
            "AFLOW"
        ]
    
    def fetch_stable_materials(
        self,
        max_atoms: int = 20,
        e_hull_threshold: float = 0.1  # eV/atom
    ) -> Dataset:
        """获取稳定材料数据集"""
        pass
```

---

## 八、下一步行动

1. **实现PhysicsGenerator**：基于diffusers库实现扩散模型
2. **集成验证管道**：连接MatterSim + DFT（VASP接口）
3. **建立数据管道**：Materials Project API集成
4. **基准测试**：MatBench/MP-20评估

---

## 来源验证

| 内容 | 来源 | 验证状态 |
|------|------|----------|
| 架构设计 | MatterGen GitHub README | ✅ 已验证 |
| S.U.N.指标 | MatterGen论文表D4 | ✅ 已验证 |
| 训练流程 | MatterGen官方文档 | ✅ 已验证 |
| 评估管道 | MatterGen evaluation/目录 | ✅ 待深入 |

---

**解析完成** | Γ | 2026-03-30
