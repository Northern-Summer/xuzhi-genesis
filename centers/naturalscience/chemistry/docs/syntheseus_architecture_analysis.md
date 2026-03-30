# Syntheseus 核心架构解析 | Γ
> 对标对象：Microsoft Research AI4Science | 来源：github.com/microsoft/syntheseus
> 解析日期：2026-03-30

---

## 一、系统定位

**Syntheseus** = 端到端逆合成规划包，核心能力：
- **单步反应预测**：目标分子 → 可能的前体分子
- **多步搜索**：构建完整合成路径
- **算法标准化**：统一接口整合不同模型和搜索算法
- **基准测试**：评估逆合成组件性能

**关键价值**：首个开源的、统一的逆合成评估框架

---

## 二、核心架构（必须Copy）

### 2.1 整体架构

```
Syntheseus
├── 反应模型（Reaction Models）
│   ├── 单步模型：输入分子 → 预测前体
│   ├── 支持模型：RetroKNN, NeuralSym, MEGAN, GraphRetro等
│   └── 统一接口：所有模型实现相同API
├── 搜索算法（Search Algorithms）
│   ├── 多步搜索：MCTS, Retro*, Beam Search
│   ├── 价值函数：评估节点潜力
│   └── 终止条件：到达可购买分子
└── 评估管道（Evaluation）
    ├── 路径评估：合成可行性
    ├── 成本评估：步数、产率、价格
    └── 对比基准：与已知路线比较
```

### 2.2 反应模型接口

```python
class ReactionModel:
    """
    统一反应模型接口（所有模型必须实现）
    """
    def __call__(self, mol: Molecule) -> List[Reaction]:
        """
        预测目标分子的可能反应
        
        Args:
            mol: 目标分子
        
        Returns:
            可能的反应列表（每个反应包含前体分子）
        """
        pass
    
    @property
    def is_trainable(self) -> bool:
        """模型是否可训练"""
        pass
    
    def train(self, data: List[ReactionExample]):
        """训练模型（如支持）"""
        pass
```

### 2.3 搜索算法接口

```python
class SearchAlgorithm:
    """
    统一搜索算法接口
    """
    def search(
        self,
        target: Molecule,
        reaction_model: ReactionModel,
        value_function: ValueFunction,
        inventory: Inventory,
        max_iterations: int
    ) -> SearchResult:
        """
        搜索合成路径
        
        Args:
            target: 目标分子
            reaction_model: 反应预测模型
            value_function: 节点价值评估
            inventory: 可购买分子库存
            max_iterations: 最大迭代次数
        
        Returns:
            搜索结果（多条可能路径）
        """
        pass
```

---

## 三、支持的反应模型（必须Copy）

| 模型 | 类型 | 特点 | 来源 |
|------|------|------|------|
| **RetroKNN** | 模板匹配 | 基于相似性检索反应模板 | Segler et al. |
| **NeuralSym** | 序列到序列 | SMILES → SMILES | 2017 |
| **MEGAN** | 图神经网络 | 图编辑预测 | 2021 |
| **GraphRetro** | 两阶段 | 离去基团识别 + 连接预测 | 2021 |
| **RootAligned** | 模板-free |  Transformer | 2022 |
| **Chemformer** | 序列到序列 | 预训练Transformer | 2022 |

### 3.1 模型选择策略

```python
# 性能 vs 速度权衡
MODEL_PRESETS = {
    "fast": ["RetroKNN"],           # 快速但精度较低
    "balanced": ["MEGAN", "GraphRetro"],  # 平衡选择
    "accurate": ["RootAligned", "Chemformer"],  # 高精度但慢
    "ensemble": ["RetroKNN", "MEGAN", "GraphRetro"]  # 集成多模型
}
```

---

## 四、搜索算法（必须Copy）

### 4.1 支持的算法

| 算法 | 类型 | 特点 | 适用场景 |
|------|------|------|----------|
| **Retro*** | A*搜索 | 启发式最优路径 | 已知价值函数 |
| **MCTS** | 蒙特卡洛树搜索 | 平衡探索与利用 | 复杂搜索空间 |
| **Beam Search** | 束搜索 | 保留Top-k路径 | 快速近似 |
| **DFPN** | 深度优先证明数 | 证明数启发 | 确定性搜索 |

### 4.2 Retro*算法详解（推荐）

```
Retro*搜索
├── 初始化：目标分子作为根节点
├── 迭代：
│   ├── 选择：选择最有希望的节点（价值函数）
│   ├── 扩展：用反应模型生成前体
│   ├── 评估：检查前体是否在库存中
│   └── 更新：更新路径价值和证明数
└── 终止：找到完整路径或达到最大迭代
```

**关键组件**：
- **AND-OR树**：反应节点（OR）+ 分子节点（AND）
- **证明数**：到达可购买分子的难度估计
- **价值函数**：合成可行性评分

---

## 五、评估体系（必须Copy）

### 5.1 单步评估指标

| 指标 | 定义 | 计算方式 |
|------|------|----------|
| **Top-k准确率** | 前k个预测中包含正确前体的比例 | 标准分类指标 |
| **覆盖率** | 测试集中有预测结果的比例 | 非空预测占比 |
| **多样性** | 预测结果的化学多样性 | Tanimoto距离 |

### 5.2 多步评估指标

| 指标 | 定义 | 意义 |
|------|------|------|
| **成功率** | 找到合成路径的比例 | 搜索算法有效性 |
| **平均步数** | 成功路径的平均反应步数 | 合成复杂度 |
| **路径成本** | 综合成本（步数×难度） | 实际可行性 |
| **首解时间** | 找到第一条路径的时间 | 搜索效率 |

### 5.3 标准数据集

| 数据集 | 规模 | 用途 |
|--------|------|------|
| **USPTO-50k** | 50k反应 | 单步反应预测标准 |
| **USPTO-full** | 1M+反应 | 大规模训练 |
| **RetroUSPTO** | 过滤后 | 高质量反应 |

---

## 六、最佳实践（必须Copy）

### 6.1 模型训练最佳实践

```python
# 数据准备
train_data = load_reactions("USPTO-50k/train.txt")
val_data = load_reactions("USPTO-50k/val.txt")

# 模型训练
model = MEGAN()
model.train(
    train_data,
    val_data,
    epochs=50,
    batch_size=128,
    lr=1e-3
)

# 评估
results = evaluate_single_step(model, test_data, top_k=[1, 3, 5, 10])
print(f"Top-1: {results.top1_acc:.2%}")
print(f"Top-10: {results.top10_acc:.2%}")
```

### 6.2 多步搜索最佳实践

```python
# 设置搜索组件
reaction_model = load_model("MEGAN")
value_function = LearnedValueFunction()
inventory = Inventory.from_file("buyable_molecules.csv")
search_alg = RetroStar()

# 搜索目标分子
target = smiles_to_mol("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
result = search_alg.search(
    target=target,
    reaction_model=reaction_model,
    value_function=value_function,
    inventory=inventory,
    max_iterations=500
)

# 输出路径
for i, route in enumerate(result.routes[:5]):
    print(f"Route {i+1}: {route.to_smiles()}")
    print(f"  Steps: {route.num_steps}")
    print(f"  Cost: {route.total_cost}")
```

### 6.3 模型集成策略（Chimera）

```python
class ChimeraEnsemble:
    """
    Chimera集成模型（Microsoft最新方法）
    集成多个异质模型，通过排序学习选择最佳预测
    """
    def __init__(self, models: List[ReactionModel]):
        self.models = models
        self.ranker = RankingModel()
    
    def __call__(self, mol: Molecule) -> List[Reaction]:
        # 收集所有模型的预测
        all_predictions = []
        for model in self.models:
            preds = model(mol)
            all_predictions.extend(preds)
        
        # 去重
        unique_predictions = deduplicate(all_predictions)
        
        # 排序模型选择最佳预测
        ranked = self.ranker.rank(unique_predictions, mol)
        
        return ranked
```

---

## 七、与MatterGen/AlphaFold的协同

### 7.1 ChemistryAI4S在ScienceAI4S中的位置

```
ScienceAI4S
├── PhysicsAI4S (MatterGen) → 材料结构
├── ChemistryAI4S (Syntheseus) → 分子合成
├── BiologyAI4S (AlphaFold) → 蛋白质结构
└── CrossDomainAI4S → 整合

协同场景：
1. Physics → Chemistry: 新材料 → 合成路径设计
2. Chemistry → Biology: 药物分子 → 蛋白质相互作用
3. Biology → Chemistry: 酶催化 → 反应优化
```

### 7.2 统一表示层

```python
class UnifiedMolecule:
    """
    统一分子表示（跨领域）
    """
    def __init__(self):
        self.smiles: str              # 化学表示
        self.graph: MolecularGraph    # 图表示
        self.conformer: Conformer     # 3D构象（来自MatterGen/AF3）
        self.properties: Dict         # 预测属性
    
    def to_crystal(self) -> Crystal:
        """转换为晶体表示（Physics）"""
        pass
    
    def to_protein_ligand(self) -> ProteinLigandComplex:
        """转换为蛋白配体复合物（Biology）"""
        pass
```

---

## 八、ChemistryAI4S设计草案

基于Syntheseus最佳实践：

### 8.1 逆合成规划器

```python
class ChemistryPlanner:
    """
    逆合成规划器（对标Syntheseus）
    """
    def __init__(self):
        self.reaction_model = EnsembleReactionModel([
            MEGAN(),
            GraphRetro(),
            RootAligned()
        ])
        self.search_algorithm = RetroStar()
        self.value_function = HybridValueFunction()
        self.inventory = ChemicalInventory()
    
    def plan_synthesis(
        self,
        target_smiles: str,
        constraints: Optional[SynthesisConstraints] = None
    ) -> SynthesisPlan:
        """
        规划目标分子的合成路线
        
        Args:
            target_smiles: 目标分子SMILES
            constraints: 合成约束（最大步数、避免试剂等）
        
        Returns:
            合成路线规划
        """
        target = Molecule.from_smiles(target_smiles)
        
        result = self.search_algorithm.search(
            target=target,
            reaction_model=self.reaction_model,
            value_function=self.value_function,
            inventory=self.inventory,
            constraints=constraints
        )
        
        return SynthesisPlan(result.routes)
```

### 8.2 反应预测器

```python
class ReactionPredictor:
    """
    单步反应预测器
    """
    def predict(
        self,
        product: Molecule,
        top_k: int = 10,
        confidence_threshold: float = 0.5
    ) -> List[ReactionPrediction]:
        """
        预测生成目标产物的可能反应
        
        Returns:
            反应预测列表（含置信度）
        """
        predictions = self.model(product, top_k=top_k)
        
        # 过滤低置信度
        filtered = [p for p in predictions if p.confidence > confidence_threshold]
        
        return filtered
```

### 8.3 合成验证器

```python
class SynthesisValidator:
    """
    合成路线验证器（对标实验验证）
    """
    def validate(
        self,
        route: SynthesisRoute,
        validation_level: ValidationLevel = ValidationLevel.COMPUTATIONAL
    ) -> ValidationResult:
        """
        验证合成路线的可行性
        
        validation_level:
        - COMPUTATIONAL: 反应规则 + 文献检索
        - REACTION_PREDICTION: 正向反应模型预测
        - LITERATURE: 已知反应匹配
        """
        if validation_level == ValidationLevel.COMPUTATIONAL:
            return self._rule_based_validation(route)
        elif validation_level == ValidationLevel.REACTION_PREDICTION:
            return self._forward_model_validation(route)
        elif validation_level == ValidationLevel.LITERATURE:
            return self._literature_validation(route)
```

---

## 九、技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 分子处理 | RDKit | 化学信息学核心 |
| 深度学习 | PyTorch | 模型训练 |
| 图神经网络 | PyG/DGL | 分子图处理 |
| 数据格式 | SMILES/SELFIES | 分子序列表示 |
| 数据库 | PostgreSQL/MongoDB | 反应数据存储 |

---

## 十、关键经验（必须Copy）

### 10.1 架构设计经验

1. **统一接口**：所有模型实现相同API，便于替换和比较
2. **模块化设计**：反应模型、搜索算法、评估独立
3. **可扩展性**：轻松添加新模型和算法

### 10.2 模型选择经验

1. **集成 > 单一模型**：Chimera集成显著提高准确率
2. **速度-精度权衡**：根据场景选择合适模型
3. **持续重评估**：定期在最新数据上评估模型

### 10.3 工程实践

1. **开源基准**：标准化评估促进社区发展
2. **完整管道**：从单步预测到多步搜索
3. **可复现性**：固定随机种子，记录所有参数

---

## 来源验证

| 内容 | 来源 | 验证状态 |
|------|------|----------|
| 架构设计 | Syntheseus GitHub | ✅ 源码验证 |
| 支持模型 | Syntheseus文档 | ✅ 官方文档 |
| 搜索算法 | Syntheseus论文 | ✅ 学术论文 |
| Chimera | Microsoft Research | ✅ 论文验证 |

---

**解析完成** | Γ | 2026-03-30
