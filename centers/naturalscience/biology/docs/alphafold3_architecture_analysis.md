# AlphaFold 3 核心架构解析 | Γ
> 对标对象：Google DeepMind | 来源：github.com/google-deepmind/alphafold3
> 解析日期：2026-03-30

---

## 一、系统定位

**AlphaFold 3** = 生物分子相互作用预测系统，核心突破：
- **统一框架**：蛋白质 + DNA + RNA + 小分子配体 + 离子
- **相互作用预测**：蛋白质-蛋白质、蛋白质-核酸、蛋白质-小分子
- **原子级精度**：2024年诺贝尔化学奖（与AlphaFold 2共同获得）

**关键差异（AF2 → AF3）**：
| 特性 | AlphaFold 2 | AlphaFold 3 |
|------|-------------|-------------|
| 分子类型 | 仅蛋白质 | 蛋白质+DNA+RNA+配体 |
| 相互作用 | 多聚体（Multimer） | 通用相互作用 |
| 小分子 | 不支持 | 支持（CCD/SMILES） |
| 共价键 | 不支持 | 支持（自定义键） |

---

## 二、核心架构（必须Copy）

### 2.1 整体架构

```
AlphaFold 3
├── 数据管道（Data Pipeline）
│   ├── 遗传搜索：Jackhmmer（蛋白质）/ Nhmmer（RNA）
│   ├── MSA构建：多序列比对
│   ├── 模板搜索：PDB结构模板
│   └── 特征生成：模型输入特征
├── 结构预测模型（Inference Model）
│   ├── 输入：序列 + MSA + 模板
│   ├── 输出：3D结构 + 置信度分数
│   └── 关键创新：Pairformer + Diffusion Module
└── 后处理
    ├── Amber松弛：局部几何优化
    └── 置信度评估：pLDDT + PAE + pTM
```

### 2.2 关键创新：Pairformer

**代替AlphaFold 2的Evoformer**

```
Pairformer架构
├── 序列表示（Single representation）
├── 配对表示（Pair representation）
└── 多层Transformer处理
    ├── 注意力机制捕获长程依赖
    └── 三角更新（Triangular updates）保持几何约束
```

**优势**：
- 更简洁的架构
- 更好的多分子类型泛化
- 更强的相互作用建模

### 2.3 关键创新：Diffusion Module（扩散模块）

**直接输出原子坐标**（而非像AF2那样输出残基间距离和角度）

```
扩散过程
├── 前向过程：逐步添加噪声到原子坐标
├── 反向过程：模型逐步去噪恢复结构
└── 输出：直接原子坐标（x, y, z）
```

**优势**：
- 通用性：适用于任何分子类型（蛋白质、DNA、RNA、小分子）
- 灵活性：自然处理配体和离子
- 精度：原子级精确预测

### 2.4 置信度指标

| 指标 | 含义 | 用途 |
|------|------|------|
| **pLDDT** | 预测局部距离差异测试 | 残基层级置信度（0-100） |
| **PAE** | 预测对齐误差 | 残基对之间的相对位置置信度 |
| **pTM** | 预测TM-score | 全局结构置信度 |
| **ipTM** | 接口pTM | 相互作用界面置信度 |

---

## 三、输入/输出规范（必须Copy）

### 3.1 输入格式（JSON）

```json
{
  "name": "Job name",
  "modelSeeds": [1, 2],
  "sequences": [
    {"protein": {"id": "A", "sequence": "PVLSCGEWQL"}},
    {"rna": {"id": "B", "sequence": "AGCU"}},
    {"dna": {"id": "C", "sequence": "GACCTCT"}},
    {"ligand": {"id": "D", "ccdCodes": ["ATP"]}},
    {"ligand": {"id": "E", "smiles": "CC(=O)OC1C[NH+]2CCC1CC2"}}
  ],
  "bondedAtomPairs": [[["A", 145, "SG"], ["D", 1, "C04"]]],
  "dialect": "alphafold3",
  "version": 4
}
```

### 3.2 输出格式

```
output/
├── ranked_0.pdb          # 最高置信度结构
├── ranked_1.pdb          # 次高置信度
├── ...
├── confidence.json       # 置信度分数
├── summary_confidences.json
└── full_data.json        # 完整预测数据
```

---

## 四、最佳实践（必须Copy）

### 4.1 MSA（多序列比对）策略

| 场景 | 策略 | 说明 |
|------|------|------|
| 标准预测 | 自动构建MSA | 使用Jackhmmer/Nhmmer搜索遗传数据库 |
| 快速预测 | MSA-free | 跳过MSA构建（精度下降） |
| 自定义 | 提供MSA | 用户提供预计算A3M格式MSA |

### 4.2 模板策略

| 场景 | 策略 | 说明 |
|------|------|------|
| 标准预测 | 自动模板搜索 | 从PDB搜索同源结构 |
| 高精度 | 自定义模板 | 提供已知高质量结构 |
| 探索性 | 模板-free | 完全基于序列预测 |

### 4.3 种子策略

**多种子运行**：
- 默认：每个模型5个种子
- 目的：捕获预测不确定性
- 选择：基于pLDDT/pTM选择最佳结构

---

## 五、数据依赖（必须Copy）

### 5.1 遗传数据库（总计~2.6TB）

| 数据库 | 大小 | 用途 |
|--------|------|------|
| BFD | ~1.8TB | 蛋白质序列搜索 |
| MGnify | ~120GB | 宏基因组序列 |
| UniRef90 | ~67GB | 蛋白质聚类 |
| UniProt | ~105GB | 蛋白质序列+注释 |
| PDB | ~238GB | 结构模板 |

### 5.2 模型参数

- **大小**：~5GB
- **格式**：JAX checkpoint
- **获取**：需向Google申请（非商业用途）

---

## 六、与Δ的MathAI4S对接点

| Δ组件 | AlphaFold 3适配 | 对接方式 |
|-------|----------------|----------|
| **枚举搜索** | 构象空间枚举 | Δ探索构象空间 → AF3评估能量 |
| **线性模型** | 序列-属性预测 | Δ预测稳定性 → AF3验证结构 |
| **对称性分析** | 对称复合物预测 | Δ分析对称性 → AF3对称约束 |
| **Lean验证** | 物理约束验证 | Δ形式化立体化学约束 |

---

## 七、BiologyAI4S设计草案

基于AlphaFold 3最佳实践，设计BiologyAI4S核心组件：

### 7.1 结构预测器（Structure Predictor）

```python
class BiologyPredictor:
    """
    生物分子结构预测器（对标AlphaFold 3）
    """
    def __init__(self):
        self.data_pipeline = DataPipeline()    # MSA + 模板搜索
        self.inference_model = AF3Model()      # 核心预测模型
        self.confidence_scorer = ConfidenceScorer()
    
    def predict(
        self,
        sequences: List[Sequence],
        run_data_pipeline: bool = True,
        model_seeds: List[int] = [1]
    ) -> PredictionResult:
        """
        预测分子结构
        
        Args:
            sequences: 分子序列列表（蛋白/DNA/RNA/配体）
            run_data_pipeline: 是否运行数据管道（MSA构建）
            model_seeds: 随机种子列表
        
        Returns:
            预测结构 + 置信度分数
        """
        # 1. 数据管道（可选）
        if run_data_pipeline:
            features = self.data_pipeline.process(sequences)
        else:
            features = self._load_precomputed_features(sequences)
        
        # 2. 推理
        predictions = []
        for seed in model_seeds:
            structure = self.inference_model.predict(features, seed)
            confidences = self.confidence_scorer.score(structure)
            predictions.append(Prediction(structure, confidences))
        
        # 3. 选择最佳预测
        best_prediction = max(predictions, key=lambda p: p.confidence.pTM)
        
        return PredictionResult(predictions, best_prediction)
```

### 7.2 数据管道（Data Pipeline）

```python
class DataPipeline:
    """
    MSA和模板构建（对标AlphaFold 3数据管道）
    """
    def __init__(self):
        self.protein_search = JackhmmerSearch()  # 蛋白质搜索
        self.rna_search = NhmmerSearch()         # RNA搜索
        self.template_search = TemplateSearch()  # 模板搜索
    
    def process(self, sequences: List[Sequence]) -> Features:
        """
        构建输入特征
        """
        features = {}
        
        for seq in sequences:
            if seq.type == "protein":
                features[seq.id] = {
                    "msa": self.protein_search.search(seq.sequence),
                    "templates": self.template_search.search(seq.sequence)
                }
            elif seq.type == "rna":
                features[seq.id] = {
                    "msa": self.rna_search.search(seq.sequence)
                }
            # DNA和配体不需要MSA
        
        return Features(features)
```

### 7.3 置信度评估器

```python
class ConfidenceScorer:
    """
    预测置信度评估（对标pLDDT/PAE/pTM）
    """
    def score(self, structure: Structure) -> Confidences:
        """
        计算置信度指标
        """
        return Confidences(
            plddt=self._compute_plddt(structure),      # 局部置信度
            pae=self._compute_pae(structure),          # 配对误差
            ptm=self._compute_ptm(structure),          # 全局置信度
            iptm=self._compute_iptm(structure)         # 界面置信度
        )
```

---

## 八、技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 深度学习框架 | JAX + Haiku | Google开源，AF3官方实现 |
| 数值计算 | NumPy | 基础数组操作 |
| 分子处理 | RDKit | 小分子构象生成 |
| 结构解析 | Biopython | PDB/mmCIF处理 |
| 遗传搜索 | HMMER | 序列比对 |
| 容器化 | Docker | 完整环境隔离 |

---

## 九、关键经验（必须Copy）

### 9.1 架构设计经验

1. **通用表示**：使用原子级表示，统一处理所有分子类型
2. **扩散模型**：直接预测坐标，而非中间几何参数
3. **置信度估计**：始终输出预测置信度，指导用户决策

### 9.2 数据工程经验

1. **MSA质量 > 模型复杂度**：高质量的MSA是准确预测的关键
2. **模板有用但有偏**：模板可提高精度，但限制新颖性
3. **多种子捕获不确定性**：不同种子反映构象异质性

### 9.3 工程实践

1. **完整容器化**：确保环境可复现
2. **模块化设计**：数据管道和推理分离
3. **渐进式发布**：AF2 → AF3，逐步扩展能力

---

## 十、与MatterGen的协同

| MatterGen（物理） | AlphaFold 3（生物） | 协同点 |
|------------------|-------------------|--------|
| 晶体结构生成 | 蛋白质结构预测 | 结构表示统一 |
| 扩散模型 | 扩散模型 | 方法迁移 |
| DFT验证 | 实验验证 | 验证流程标准化 |
| 属性约束生成 | 序列约束预测 | 条件化方法共享 |

---

## 来源验证

| 内容 | 来源 | 验证状态 |
|------|------|----------|
| Pairformer架构 | AlphaFold 3论文（Nature 2024） | ✅ GitHub源码验证 |
| 扩散模块 | AlphaFold 3论文 | ✅ GitHub源码验证 |
| 输入格式 | AlphaFold 3 GitHub docs/input.md | ✅ 官方文档 |
| 置信度指标 | AlphaFold 3 GitHub | ✅ 官方文档 |

---

**解析完成** | Γ | 2026-03-30
