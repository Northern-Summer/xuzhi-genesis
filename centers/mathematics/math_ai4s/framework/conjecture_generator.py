#!/usr/bin/env python3
"""
ConjectureGenerator — Intelligent Conjecture Generation
猜想生成器 —— 智能猜想生成

设计哲学：
- 基于失败模式生成"几乎正确"的猜想
- 从数据中发现统计规律
- 猜想应有可证伪性和研究价值

Author: Δ (Delta-Forge)
Date: 2026-03-30
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
import json
import random
from collections import defaultdict


class ConjectureType(Enum):
    """猜想类型"""
    IMPLICATION = auto()        # 蕴含关系猜想
    EQUIVALENCE = auto()       # 等价关系猜想
    NON_IMPLICATION = auto()   # 不蕴含猜想
    STRUCTURAL = auto()        # 结构性质猜想
    ANALOGY = auto()           # 类比猜想


class ConjecturePriority(Enum):
    """猜想优先级（研究价值）"""
    CRITICAL = 5    # 关键猜想，可能解决多个open问题
    HIGH = 4        # 高价值，有重要理论意义
    MEDIUM = 3      # 中等价值，值得研究
    LOW = 2         # 低价值，但有可证性
    TRIVIAL = 1     # 平凡猜想，主要作为练习


@dataclass
class Conjecture:
    """猜想记录"""
    conjecture_id: str
    conjecture_type: ConjectureType
    
    # 猜想内容
    statement: str                      # 人类可读的陈述
    formal_statement: Optional[str]     # 形式化陈述（Lean）
    
    # 涉及对象
    from_eq: Optional[int] = None
    to_eq: Optional[int] = None
    related_equations: List[int] = field(default_factory=list)
    
    # 优先级与价值
    priority: ConjecturePriority = ConjecturePriority.MEDIUM
    confidence: float = 0.5             # 置信度 0.0-1.0
    
    # 支持证据
    evidence: List[Dict] = field(default_factory=list)
    """
    evidence = [
        {
            "type": "statistical",      # statistical, analogical, structural
            "source": "pattern_analysis",
            "strength": 0.8,
            "details": {...}
        }
    ]
    """
    
    # 生成信息
    generation_method: str = ""         # 生成方法
    based_on_failures: List[str] = field(default_factory=list)  # 基于的失败记录
    
    # 验证状态
    status: str = "open"                # open, proven, refuted, investigating
    verification_attempts: int = 0
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "conjecture_id": self.conjecture_id,
            "conjecture_type": self.conjecture_type.name,
            "statement": self.statement,
            "formal_statement": self.formal_statement,
            "from_eq": self.from_eq,
            "to_eq": self.to_eq,
            "related_equations": self.related_equations,
            "priority": self.priority.name,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "generation_method": self.generation_method,
            "based_on_failures": self.based_on_failures,
            "status": self.status,
            "verification_attempts": self.verification_attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "session_id": self.session_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Conjecture":
        return cls(
            conjecture_id=data["conjecture_id"],
            conjecture_type=ConjectureType[data["conjecture_type"]],
            statement=data["statement"],
            formal_statement=data.get("formal_statement"),
            from_eq=data.get("from_eq"),
            to_eq=data.get("to_eq"),
            related_equations=data.get("related_equations", []),
            priority=ConjecturePriority[data.get("priority", "MEDIUM")],
            confidence=data.get("confidence", 0.5),
            evidence=data.get("evidence", []),
            generation_method=data.get("generation_method", ""),
            based_on_failures=data.get("based_on_failures", []),
            status=data.get("status", "open"),
            verification_attempts=data.get("verification_attempts", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            session_id=data.get("session_id", ""),
        )


@dataclass
class PatternHypothesis:
    """模式假设（中间产物）"""
    hypothesis_id: str
    description: str
    
    # 适用范围
    applicable_equations: List[int] = field(default_factory=list)
    
    # 统计支持
    supporting_cases: int = 0
    contradicting_cases: int = 0
    unknown_cases: int = 0
    
    # 置信度
    confidence: float = 0.0
    
    @property
    def total_cases(self) -> int:
        return self.supporting_cases + self.contradicting_cases + self.unknown_cases
    
    @property
    def support_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.supporting_cases / self.total_cases


class ConjectureGenerator:
    """猜想生成器主类"""
    
    def __init__(self, 
                 knowledge_graph=None,
                 failure_analyzer=None,
                 storage_path: Optional[Path] = None):
        """
        初始化猜想生成器
        
        Args:
            knowledge_graph: 知识图谱实例
            failure_analyzer: 失败分析器实例
            storage_path: 存储路径
        """
        self.kg = knowledge_graph
        self.fa = failure_analyzer
        
        if storage_path is None:
            storage_path = Path.home() / ".xuzhi_memory" / "agents" / "delta" / "conjectures"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.conjectures: Dict[str, Conjecture] = {}
        self.hypotheses: Dict[str, PatternHypothesis] = {}
        
        self._load_conjectures()
    
    def _load_conjectures(self):
        """加载历史猜想"""
        conj_file = self.storage_path / "conjectures.jsonl"
        if conj_file.exists():
            with open(conj_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            conj = Conjecture.from_dict(data)
                            self.conjectures[conj.conjecture_id] = conj
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Failed to load conjecture: {e}")
    
    # ========== 猜想生成方法 ==========
    
    def generate_from_failure_patterns(self, 
                                       target_equations: List[int] = None,
                                       max_conjectures: int = 10) -> List[Conjecture]:
        """
        从失败模式生成猜想
        
        思路：
        - 如果某类问题（如Eq65相关的implication）经常在小magma搜索中失败
        - 猜想：这类问题可能需要更大阶的magma或完全不同的方法
        - 或者猜想：这类implication实际上成立（否则应该已经找到反例）
        """
        if self.fa is None:
            return []
        
        conjectures = []
        
        # 获取失败模式统计
        report = self.fa.generate_failure_report()
        
        # 分析"EFFORT_EXHAUSTED"类型的失败
        # 这些可能是实际上成立但难以证明的implication
        for record in self.fa.records.values():
            if record.failure_type.name == "EFFORT_EXHAUSTED":
                # 生成"可能成立"的猜想
                conj = self._create_implication_conjecture(
                    from_eq=record.from_eq,
                    to_eq=record.to_eq,
                    confidence=0.6,  # 中等置信度
                    reason=f"Failed to find counterexample despite extensive search ({record.effort_spent} efforts)",
                    based_on=[record.failure_id],
                    priority=ConjecturePriority.MEDIUM,
                )
                conjectures.append(conj)
                
                if len(conjectures) >= max_conjectures:
                    break
        
        return conjectures
    
    def generate_from_transitivity(self,
                                   known_implications: List[Tuple[int, int]] = None) -> List[Conjecture]:
        """
        基于传递性生成猜想
        
        思路：
        - 如果 EqA → EqB 和 EqB → EqC 都已知
        - 则 EqA → EqC 应该成立（如果还没被证明）
        """
        conjectures = []
        
        if known_implications is None and self.kg:
            # 从知识图谱获取已知implication
            known_implications = [
                (n.content["from_eq"], n.content["to_eq"])
                for n in self.kg.nodes.values()
                if n.node_type.name == "EQUATION_PAIR" 
                and n.content.get("status") == "proven"
            ]
        
        if not known_implications:
            return conjectures
        
        # 构建传递闭包
        implication_graph = defaultdict(set)
        for from_eq, to_eq in known_implications:
            implication_graph[from_eq].add(to_eq)
        
        # 查找传递路径
        for eq_a in implication_graph:
            for eq_b in implication_graph[eq_a]:
                for eq_c in implication_graph[eq_b]:
                    if eq_c not in implication_graph[eq_a]:
                        # 发现潜在的传递implication
                        conj = self._create_implication_conjecture(
                            from_eq=eq_a,
                            to_eq=eq_c,
                            confidence=0.9,  # 高置信度（传递性）
                            reason=f"Transitivity: {eq_a} → {eq_b} → {eq_c}",
                            priority=ConjecturePriority.HIGH,
                        )
                        conjectures.append(conj)
        
        return conjectures
    
    def generate_from_structural_similarity(self,
                                            equation_groups: List[List[int]] = None) -> List[Conjecture]:
        """
        基于结构相似性生成猜想
        
        思路：
        - 结构相似的方程可能具有相似的implication性质
        - 例如：都包含嵌套运算的方程可能共享某些性质
        """
        conjectures = []
        
        # 简单的分组策略（实际可以更复杂）
        if equation_groups is None:
            # 从知识图谱自动分组
            if self.kg:
                # 基于已知implication的连通性分组
                equation_groups = self._cluster_by_implications()
        
        if not equation_groups:
            return conjectures
        
        # 对每个组，如果组内某个implication成立，猜想其他相似implication也成立
        for group in equation_groups:
            if len(group) < 2:
                continue
            
            # 查找组内已知的implication
            known_impls = []
            if self.kg:
                for i, eq_a in enumerate(group):
                    for eq_b in group[i+1:]:
                        status = self.kg.get_implication_status(eq_a, eq_b)
                        if status == "proven":
                            known_impls.append((eq_a, eq_b))
            
            # 基于已知implication生成类比猜想
            for known_a, known_b in known_impls:
                for eq in group:
                    if eq != known_a and eq != known_b:
                        # 猜想：相似结构的方程可能有相似性质
                        conj = Conjecture(
                            conjecture_id=f"CONJ_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}",
                            conjecture_type=ConjectureType.ANALOGY,
                            statement=f"Equations structurally similar to {known_a} and {known_b} may share implication properties",
                            from_eq=None,  # 不是具体implication
                            to_eq=None,
                            related_equations=[known_a, known_b, eq],
                            priority=ConjecturePriority.LOW,
                            confidence=0.4,
                            evidence=[{
                                "type": "structural_similarity",
                                "source": "cluster_analysis",
                                "strength": 0.4,
                                "details": {
                                    "known_pair": (known_a, known_b),
                                    "similar_equation": eq,
                                    "cluster": group,
                                }
                            }],
                            generation_method="structural_similarity",
                        )
                        conjectures.append(conj)
        
        return conjectures
    
    def generate_high_value_targets(self,
                                    open_problems: List[Tuple[int, int]] = None,
                                    max_conjectures: int = 5) -> List[Conjecture]:
        """
        生成高价值研究目标
        
        思路：
        - 能证明/否定大量其他implication的"枢纽"方程
        - 类似于图论中的关键节点
        """
        conjectures = []
        
        if open_problems is None:
            # 获取所有open的implication
            if self.kg:
                open_problems = [
                    (n.content["from_eq"], n.content["to_eq"])
                    for n in self.kg.nodes.values()
                    if n.node_type.name == "EQUATION_PAIR"
                    and n.content.get("status") == "unknown"
                ]
        
        if not open_problems:
            return conjectures
        
        # 分析哪些方程作为"中间点"出现频率最高
        from_counts = defaultdict(int)
        to_counts = defaultdict(int)
        
        for from_eq, to_eq in open_problems:
            from_counts[from_eq] += 1
            to_counts[to_eq] += 1
        
        # 找出关键方程（连接度最高的）
        all_equations = set(from_counts.keys()) | set(to_counts.keys())
        centrality = {
            eq: from_counts.get(eq, 0) + to_counts.get(eq, 0)
            for eq in all_equations
        }
        
        # 生成关于关键方程的猜想
        top_equations = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:max_conjectures]
        
        for eq_id, degree in top_equations:
            conj = Conjecture(
                conjecture_id=f"CONJ_HUB_{eq_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                conjecture_type=ConjectureType.STRUCTURAL,
                statement=f"Equation {eq_id} is a structural hub (degree {degree}), understanding it may resolve {degree} open implications",
                related_equations=[eq_id],
                priority=ConjecturePriority.CRITICAL if degree > 10 else ConjecturePriority.HIGH,
                confidence=0.7,
                evidence=[{
                    "type": "graph_analysis",
                    "source": "centrality_analysis",
                    "strength": min(degree / 20, 1.0),
                    "details": {
                        "equation": eq_id,
                        "out_degree": from_counts.get(eq_id, 0),
                        "in_degree": to_counts.get(eq_id, 0),
                        "total_degree": degree,
                    }
                }],
                generation_method="centrality_analysis",
            )
            conjectures.append(conj)
        
        return conjectures
    
    def generate_all(self, 
                     target_equations: List[int] = None,
                     max_per_method: int = 5) -> List[Conjecture]:
        """
        使用所有方法生成猜想
        
        Returns:
            按优先级和置信度排序的猜想列表
        """
        all_conjectures = []
        
        # 方法1：从失败模式
        all_conjectures.extend(
            self.generate_from_failure_patterns(target_equations, max_per_method)
        )
        
        # 方法2：传递性
        all_conjectures.extend(
            self.generate_from_transitivity()
        )
        
        # 方法3：结构相似性
        all_conjectures.extend(
            self.generate_from_structural_similarity()
        )
        
        # 方法4：高价值目标
        all_conjectures.extend(
            self.generate_high_value_targets(max_conjectures=max_per_method)
        )
        
        # 去重（基于implication）
        seen_implications = set()
        unique_conjectures = []
        
        for conj in all_conjectures:
            key = (conj.from_eq, conj.to_eq, conj.conjecture_type.name)
            if key not in seen_implications or conj.from_eq is None:
                seen_implications.add(key)
                unique_conjectures.append(conj)
                self._save_conjecture(conj)
        
        # 排序：优先级高 -> 置信度高
        unique_conjectures.sort(
            key=lambda c: (c.priority.value, c.confidence),
            reverse=True
        )
        
        return unique_conjectures
    
    # ========== 辅助方法 ==========
    
    def _create_implication_conjecture(self,
                                       from_eq: int,
                                       to_eq: int,
                                       confidence: float,
                                       reason: str,
                                       based_on: List[str] = None,
                                       priority: ConjecturePriority = ConjecturePriority.MEDIUM) -> Conjecture:
        """创建implication猜想"""
        conj_id = f"CONJ_{from_eq}_{to_eq}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return Conjecture(
            conjecture_id=conj_id,
            conjecture_type=ConjectureType.IMPLICATION,
            statement=f"Conjecture: Equation {from_eq} implies Equation {to_eq}. Reason: {reason}",
            formal_statement=f"Equation{from_eq}_implies_Equation{to_eq}",
            from_eq=from_eq,
            to_eq=to_eq,
            priority=priority,
            confidence=confidence,
            evidence=[{
                "type": "pattern_analysis",
                "source": "failure_analysis",
                "strength": confidence,
                "details": {"reason": reason}
            }],
            generation_method="failure_pattern_analysis",
            based_on_failures=based_on or [],
        )
    
    def _cluster_by_implications(self) -> List[List[int]]:
        """基于implication关系聚类方程"""
        if not self.kg:
            return []
        
        # 获取所有方程
        equations = set()
        for node in self.kg.nodes.values():
            if node.node_type.name == "EQUATION":
                eq_id = node.content.get("equation_id")
                if eq_id is not None:
                    equations.add(eq_id)
        
        # 简单的连通分量聚类
        visited = set()
        clusters = []
        
        def dfs(eq, cluster):
            if eq in visited:
                return
            visited.add(eq)
            cluster.append(eq)
            
            # 找邻居
            for edge in self.kg.edges.values():
                if edge.edge_type.name in ["IMPLIES", "SPECIALIZATION"]:
                    if edge.from_node == f"EQ{eq}":
                        neighbor_id = edge.to_node
                        if neighbor_id.startswith("EQ"):
                            try:
                                neighbor_eq = int(neighbor_id[2:])
                                dfs(neighbor_eq, cluster)
                            except ValueError:
                                pass
        
        for eq in equations:
            if eq not in visited:
                cluster = []
                dfs(eq, cluster)
                if cluster:
                    clusters.append(cluster)
        
        return clusters
    
    def _save_conjecture(self, conj: Conjecture):
        """保存猜想到磁盘"""
        self.conjectures[conj.conjecture_id] = conj
        
        conj_file = self.storage_path / "conjectures.jsonl"
        with open(conj_file, 'a') as f:
            f.write(json.dumps(conj.to_dict(), ensure_ascii=False) + '\n')
    
    # ========== 查询与报告 ==========
    
    def get_conjectures_by_priority(self, 
                                    min_priority: ConjecturePriority = ConjecturePriority.LOW) -> List[Conjecture]:
        """按优先级获取猜想"""
        return [
            c for c in self.conjectures.values()
            if c.priority.value >= min_priority.value
            and c.status == "open"
        ]
    
    def get_conjectures_for_equation(self, eq_id: int) -> List[Conjecture]:
        """获取涉及特定方程的所有猜想"""
        return [
            c for c in self.conjectures.values()
            if c.from_eq == eq_id 
            or c.to_eq == eq_id
            or eq_id in c.related_equations
        ]
    
    def mark_verification_attempt(self, conjecture_id: str, 
                                   success: bool,
                                   proof_data: Dict = None):
        """标记猜想验证尝试"""
        if conjecture_id in self.conjectures:
            conj = self.conjectures[conjecture_id]
            conj.verification_attempts += 1
            conj.updated_at = datetime.now().isoformat()
            
            if success:
                conj.status = "proven"
            elif conj.verification_attempts >= 3:
                # 多次尝试失败，可能需要重新评估
                conj.status = "investigating"
            
            # 更新存储
            self._update_conjecture_file()
    
    def _update_conjecture_file(self):
        """更新猜想文件（重写）"""
        conj_file = self.storage_path / "conjectures.jsonl"
        with open(conj_file, 'w') as f:
            for conj in self.conjectures.values():
                f.write(json.dumps(conj.to_dict(), ensure_ascii=False) + '\n')
    
    def generate_report(self) -> Dict:
        """生成猜想生成报告"""
        return {
            "total_conjectures": len(self.conjectures),
            "by_type": {
                ct.name: len([c for c in self.conjectures.values() if c.conjecture_type == ct])
                for ct in ConjectureType
            },
            "by_priority": {
                cp.name: len([c for c in self.conjectures.values() if c.priority == cp])
                for cp in ConjecturePriority
            },
            "by_status": {
                status: len([c for c in self.conjectures.values() if c.status == status])
                for status in ["open", "proven", "refuted", "investigating"]
            },
            "top_conjectures": [
                c.to_dict() for c in sorted(
                    self.conjectures.values(),
                    key=lambda x: (x.priority.value, x.confidence),
                    reverse=True
                )[:10]
            ],
        }


# 便捷函数
def create_conjecture_generator(knowledge_graph=None, failure_analyzer=None) -> ConjectureGenerator:
    """创建默认猜想生成器"""
    return ConjectureGenerator(
        knowledge_graph=knowledge_graph,
        failure_analyzer=failure_analyzer
    )


if __name__ == "__main__":
    # 测试
    cg = create_conjecture_generator()
    
    # 生成一些猜想
    conjectures = cg.generate_all(max_per_method=2)
    
    print(f"Generated {len(conjectures)} conjectures:")
    for conj in conjectures[:5]:
        print(f"  - [{conj.priority.name}] {conj.statement[:80]}...")
    
    print(f"\nReport:")
    print(json.dumps(cg.generate_report(), indent=2))
