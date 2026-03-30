#!/usr/bin/env python3
"""
KnowledgeGraph — Experience Storage and Retrieval
知识图谱 —— 经验存储与检索

设计哲学：
- 不仅仅是数据库，是经验的结构化网络
- 支持类比推理："这个问题像之前解决过的那个"
- 避免重复劳动，复用已有成果

Author: Δ (Delta-Forge)
Date: 2026-03-30
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
from collections import defaultdict
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
import json
import hashlib
import pickle


class NodeType(Enum):
    """知识节点类型"""
    EQUATION = auto()           # 方程
    EQUATION_PAIR = auto()      # 方程对（implication）
    MAGMA = auto()              # Magma结构
    PROOF = auto()              # 证明
    COUNTEREXAMPLE = auto()     # 反例
    STRATEGY = auto()           # 探索策略
    PATTERN = auto()            # 模式（成功或失败）
    CONJECTURE = auto()         # 猜想


class EdgeType(Enum):
    """知识边类型"""
    # 逻辑关系
    IMPLIES = auto()            # 蕴含
    NOT_IMPLIES = auto()        # 不蕴含
    EQUIVALENT = auto()         # 等价
    
    # 证明关系
    PROVED_BY = auto()          # 被...证明
    REFUTED_BY = auto()         # 被...否定
    
    # 结构关系
    INSTANCE_OF = auto()        # 是...的实例
    GENERALIZATION = auto()     # 泛化
    SPECIALIZATION = auto()     # 特化
    
    # 探索关系
    EXPLORED_WITH = auto()      # 用...探索
    SUCCEEDED_WITH = auto()     # 用...成功
    FAILED_WITH = auto()        # 用...失败
    
    # 相似关系
    SIMILAR_TO = auto()         # 相似于
    ANALOGY = auto()            # 类比
    
    # 依赖关系
    DEPENDS_ON = auto()         # 依赖于
    USED_IN = auto()            # 被用于


@dataclass
class KnowledgeNode:
    """知识节点"""
    node_id: str
    node_type: NodeType
    
    # 内容
    content: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = ""             # 来源（ETP、Vampire、Mace4等）
    confidence: float = 1.0      # 置信度 (0.0-1.0)
    
    # 验证状态
    verification_level: str = "none"  # none, computational, atp, lean
    verified_by: List[str] = field(default_factory=list)  # 验证者列表
    
    # 访问统计
    access_count: int = 0
    last_accessed: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.name,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "confidence": self.confidence,
            "verification_level": self.verification_level,
            "verified_by": self.verified_by,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeNode":
        return cls(
            node_id=data["node_id"],
            node_type=NodeType[data["node_type"]],
            content=data.get("content", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            source=data.get("source", ""),
            confidence=data.get("confidence", 1.0),
            verification_level=data.get("verification_level", "none"),
            verified_by=data.get("verified_by", []),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
        )


@dataclass
class KnowledgeEdge:
    """知识边"""
    edge_id: str
    edge_type: EdgeType
    from_node: str
    to_node: str
    
    # 权重（相似度、强度等）
    weight: float = 1.0
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = ""
    evidence: List[str] = field(default_factory=list)  # 支持证据
    
    def to_dict(self) -> Dict:
        return {
            "edge_id": self.edge_id,
            "edge_type": self.edge_type.name,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "weight": self.weight,
            "created_at": self.created_at,
            "source": self.source,
            "evidence": self.evidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeEdge":
        return cls(
            edge_id=data["edge_id"],
            edge_type=EdgeType[data["edge_type"]],
            from_node=data["from_node"],
            to_node=data["to_node"],
            weight=data.get("weight", 1.0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            source=data.get("source", ""),
            evidence=data.get("evidence", []),
        )


@dataclass
class ExplorationExperience:
    """探索经验（用于复用）"""
    experience_id: str
    
    # 问题描述
    from_eq: int
    to_eq: int
    
    # 结果
    succeeded: bool
    result_type: str  # "proven", "refuted", "unknown"
    
    # 使用的策略和参数
    strategy: str
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    
    # 关键发现
    key_insight: str = ""        # 人类可读的关键洞察
    key_structure: Optional[Dict] = None  # 关键结构（如反例的magma）
    
    # 可复用性评估
    reusability_score: float = 0.0  # 0.0-1.0，越高越可能复用
    applicable_to: List[Tuple[int, int]] = field(default_factory=list)  # 适用的问题列表
    
    # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "experience_id": self.experience_id,
            "from_eq": self.from_eq,
            "to_eq": self.to_eq,
            "succeeded": self.succeeded,
            "result_type": self.result_type,
            "strategy": self.strategy,
            "strategy_params": self.strategy_params,
            "key_insight": self.key_insight,
            "key_structure": self.key_structure,
            "reusability_score": self.reusability_score,
            "applicable_to": self.applicable_to,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExplorationExperience":
        return cls(
            experience_id=data["experience_id"],
            from_eq=data["from_eq"],
            to_eq=data["to_eq"],
            succeeded=data["succeeded"],
            result_type=data["result_type"],
            strategy=data["strategy"],
            strategy_params=data.get("strategy_params", {}),
            key_insight=data.get("key_insight", ""),
            key_structure=data.get("key_structure"),
            reusability_score=data.get("reusability_score", 0.0),
            applicable_to=data.get("applicable_to", []),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            session_id=data.get("session_id", ""),
        )


class KnowledgeGraph:
    """知识图谱主类"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化知识图谱
        
        Args:
            storage_path: 存储路径
        """
        if storage_path is None:
            storage_path = Path.home() / ".xuzhi_memory" / "agents" / "delta" / "knowledge_graph"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        self.experiences: Dict[str, ExplorationExperience] = {}
        
        # 索引
        self._equation_index: Dict[int, str] = {}  # eq_id -> node_id
        self._implication_index: Dict[Tuple[int, int], str] = {}  # (from, to) -> node_id
        self._strategy_index: Dict[str, List[str]] = defaultdict(list)  # strategy -> experience_ids
        
        self._load_data()
    
    def _load_data(self):
        """从磁盘加载数据"""
        # 加载节点
        nodes_file = self.storage_path / "nodes.jsonl"
        if nodes_file.exists():
            with open(nodes_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            node = KnowledgeNode.from_dict(data)
                            self.nodes[node.node_id] = node
                            
                            # 更新索引
                            if node.node_type == NodeType.EQUATION:
                                eq_id = node.content.get("equation_id")
                                if eq_id is not None:
                                    self._equation_index[eq_id] = node.node_id
                            elif node.node_type == NodeType.EQUATION_PAIR:
                                pair = node.content.get("pair")
                                if pair:
                                    self._implication_index[tuple(pair)] = node.node_id
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Failed to load node: {e}")
        
        # 加载边
        edges_file = self.storage_path / "edges.jsonl"
        if edges_file.exists():
            with open(edges_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            edge = KnowledgeEdge.from_dict(data)
                            self.edges[edge.edge_id] = edge
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Failed to load edge: {e}")
        
        # 加载经验
        experiences_file = self.storage_path / "experiences.jsonl"
        if experiences_file.exists():
            with open(experiences_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            exp = ExplorationExperience.from_dict(data)
                            self.experiences[exp.experience_id] = exp
                            self._strategy_index[exp.strategy].append(exp.experience_id)
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Failed to load experience: {e}")
    
    # ========== 节点管理 ==========
    
    def add_equation(self, eq_id: int, lean_notation: str, 
                     human_readable: str = "",
                     source: str = "") -> KnowledgeNode:
        """添加方程节点"""
        node_id = f"EQ{eq_id}"
        
        if node_id in self.nodes:
            return self.nodes[node_id]
        
        node = KnowledgeNode(
            node_id=node_id,
            node_type=NodeType.EQUATION,
            content={
                "equation_id": eq_id,
                "lean_notation": lean_notation,
                "human_readable": human_readable,
            },
            source=source,
        )
        
        self.nodes[node_id] = node
        self._equation_index[eq_id] = node_id
        self._save_node(node)
        
        return node
    
    def add_implication(self, from_eq: int, to_eq: int,
                        status: str = "unknown",  # unknown, proven, refuted, conjecture
                        source: str = "") -> KnowledgeNode:
        """添加implication节点"""
        node_id = f"IMP{from_eq}_{to_eq}"
        
        if node_id in self.nodes:
            # 更新状态
            self.nodes[node_id].content["status"] = status
            self.nodes[node_id].updated_at = datetime.now().isoformat()
            return self.nodes[node_id]
        
        node = KnowledgeNode(
            node_id=node_id,
            node_type=NodeType.EQUATION_PAIR,
            content={
                "pair": [from_eq, to_eq],
                "from_eq": from_eq,
                "to_eq": to_eq,
                "status": status,
            },
            source=source,
        )
        
        self.nodes[node_id] = node
        self._implication_index[(from_eq, to_eq)] = node_id
        self._save_node(node)
        
        # 添加边连接到方程
        self._ensure_equation_exists(from_eq)
        self._ensure_equation_exists(to_eq)
        self.add_edge(f"EQ{from_eq}", node_id, EdgeType.SPECIALIZATION, weight=1.0)
        self.add_edge(f"EQ{to_eq}", node_id, EdgeType.SPECIALIZATION, weight=1.0)
        
        return node
    
    def _ensure_equation_exists(self, eq_id: int):
        """确保方程节点存在"""
        if eq_id not in self._equation_index:
            self.add_equation(eq_id, f"Equation{eq_id}", source="auto")
    
    def add_magma(self, magma_data: Dict, 
                  satisfies: List[int] = None,
                  violates: List[int] = None) -> KnowledgeNode:
        """添加magma节点"""
        # 生成唯一ID
        table_str = json.dumps(magma_data.get("multiplication_table", {}), sort_keys=True)
        node_id = f"MAG{hashlib.sha256(table_str.encode()).hexdigest()[:12]}"
        
        if node_id in self.nodes:
            return self.nodes[node_id]
        
        node = KnowledgeNode(
            node_id=node_id,
            node_type=NodeType.MAGMA,
            content={
                "order": magma_data.get("order"),
                "multiplication_table": magma_data.get("multiplication_table"),
                "satisfies": satisfies or [],
                "violates": violates or [],
            },
        )
        
        self.nodes[node_id] = node
        self._save_node(node)
        
        # 添加边连接到方程
        for eq_id in (satisfies or []):
            self._ensure_equation_exists(eq_id)
            self.add_edge(node_id, f"EQ{eq_id}", EdgeType.INSTANCE_OF)
        
        return node
    
    # ========== 边管理 ==========
    
    def add_edge(self, from_node: str, to_node: str, 
                 edge_type: EdgeType, weight: float = 1.0,
                 source: str = "", evidence: List[str] = None) -> KnowledgeEdge:
        """添加边"""
        edge_id = f"{from_node}_{edge_type.name}_{to_node}"
        
        if edge_id in self.edges:
            # 更新权重
            self.edges[edge_id].weight = max(self.edges[edge_id].weight, weight)
            return self.edges[edge_id]
        
        edge = KnowledgeEdge(
            edge_id=edge_id,
            edge_type=edge_type,
            from_node=from_node,
            to_node=to_node,
            weight=weight,
            source=source,
            evidence=evidence or [],
        )
        
        self.edges[edge_id] = edge
        self._save_edge(edge)
        
        return edge
    
    # ========== 经验管理 ==========
    
    def record_experience(self, from_eq: int, to_eq: int,
                          succeeded: bool, result_type: str,
                          strategy: str, strategy_params: Dict = None,
                          key_insight: str = "", key_structure: Dict = None,
                          applicable_equations: List[Tuple[int, int]] = None,
                          session_id: str = "") -> ExplorationExperience:
        """记录探索经验"""
        exp_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}_{from_eq}_{to_eq}"
        
        # 计算可复用性分数
        reusability = self._compute_reusability(
            succeeded, result_type, strategy, key_structure
        )
        
        exp = ExplorationExperience(
            experience_id=exp_id,
            from_eq=from_eq,
            to_eq=to_eq,
            succeeded=succeeded,
            result_type=result_type,
            strategy=strategy,
            strategy_params=strategy_params or {},
            key_insight=key_insight,
            key_structure=key_structure,
            reusability_score=reusability,
            applicable_to=applicable_equations or [],
            session_id=session_id,
        )
        
        self.experiences[exp_id] = exp
        self._strategy_index[strategy].append(exp_id)
        self._save_experience(exp)
        
        # 更新知识图谱
        self.add_implication(from_eq, to_eq, status=result_type, source="experience")
        
        return exp
    
    def _compute_reusability(self, succeeded: bool, result_type: str,
                             strategy: str, key_structure: Optional[Dict]) -> float:
        """计算经验可复用性分数"""
        score = 0.0
        
        # 成功结果更可能复用
        if succeeded:
            score += 0.3
        
        # 有明确结果类型
        if result_type in ["proven", "refuted"]:
            score += 0.3
        
        # 有具体结构（如反例）更容易复用
        if key_structure:
            score += 0.2
        
        # 某些策略更容易复用
        reusable_strategies = ["SmallMagmaEnumeration", "LinearModelStrategy"]
        if strategy in reusable_strategies:
            score += 0.2
        
        return min(score, 1.0)
    
    def find_similar_experiences(self, from_eq: int, to_eq: int,
                                  strategy: str = None,
                                  top_k: int = 5) -> List[ExplorationExperience]:
        """查找相似经验"""
        candidates = []
        
        for exp in self.experiences.values():
            # 直接匹配
            if exp.from_eq == from_eq and exp.to_eq == to_eq:
                candidates.append((exp, 1.0))
                continue
            
            # 适用列表匹配
            if (from_eq, to_eq) in exp.applicable_to:
                candidates.append((exp, 0.9))
                continue
            
            # 策略匹配
            if strategy and exp.strategy == strategy:
                # 计算方程相似度（简单的ID差值）
                eq_sim = 1.0 / (1 + abs(exp.from_eq - from_eq) + abs(exp.to_eq - to_eq))
                candidates.append((exp, eq_sim * 0.5))
        
        # 排序并返回top_k
        candidates.sort(key=lambda x: (x[0].reusability_score * x[1]), reverse=True)
        return [exp for exp, _ in candidates[:top_k]]
    
    def get_strategy_effectiveness(self, strategy: str) -> Dict:
        """获取策略有效性统计"""
        exp_ids = self._strategy_index.get(strategy, [])
        
        if not exp_ids:
            return {"usage": 0, "success_rate": 0.0, "avg_reusability": 0.0}
        
        exps = [self.experiences[eid] for eid in exp_ids]
        successes = sum(1 for e in exps if e.succeeded)
        
        return {
            "usage": len(exps),
            "success_rate": successes / len(exps),
            "avg_reusability": sum(e.reusability_score for e in exps) / len(exps),
            "by_result_type": {
                rt: len([e for e in exps if e.result_type == rt])
                for rt in set(e.result_type for e in exps)
            },
        }
    
    # ========== 查询功能 ==========
    
    def get_implication_status(self, from_eq: int, to_eq: int) -> Optional[str]:
        """获取implication状态"""
        node_id = self._implication_index.get((from_eq, to_eq))
        if node_id and node_id in self.nodes:
            return self.nodes[node_id].content.get("status")
        return None
    
    def get_neighbors(self, node_id: str, 
                      edge_type: EdgeType = None) -> List[Tuple[KnowledgeNode, float]]:
        """获取邻居节点"""
        neighbors = []
        
        for edge in self.edges.values():
            if edge.from_node == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    if edge.to_node in self.nodes:
                        neighbors.append((self.nodes[edge.to_node], edge.weight))
        
        return sorted(neighbors, key=lambda x: x[1], reverse=True)
    
    def find_path(self, from_eq: int, to_eq: int, 
                  max_length: int = 3) -> List[List[str]]:
        """
        查找方程间的蕴含路径
        
        例如：Eq1 → Eq2 → Eq3 表示 Eq1 implies Eq3 (传递性)
        """
        start_id = self._equation_index.get(from_eq)
        end_id = self._equation_index.get(to_eq)
        
        if not start_id or not end_id:
            return []
        
        # BFS查找路径
        paths = []
        queue = [(start_id, [start_id])]
        visited = {start_id}
        
        while queue and len(paths) < 10:  # 限制路径数量
            current, path = queue.pop(0)
            
            if current == end_id and len(path) > 1:
                paths.append(path)
                continue
            
            if len(path) >= max_length:
                continue
            
            # 找蕴含边
            for edge in self.edges.values():
                if edge.from_node == current and edge.edge_type in [EdgeType.IMPLIES, EdgeType.SPECIALIZATION]:
                    next_node = edge.to_node
                    if next_node not in visited:
                        visited.add(next_node)
                        queue.append((next_node, path + [next_node]))
        
        return paths
    
    # ========== 存储 ==========
    
    def _save_node(self, node: KnowledgeNode):
        """保存节点"""
        nodes_file = self.storage_path / "nodes.jsonl"
        with open(nodes_file, 'a') as f:
            f.write(json.dumps(node.to_dict(), ensure_ascii=False) + '\n')
    
    def _save_edge(self, edge: KnowledgeEdge):
        """保存边"""
        edges_file = self.storage_path / "edges.jsonl"
        with open(edges_file, 'a') as f:
            f.write(json.dumps(edge.to_dict(), ensure_ascii=False) + '\n')
    
    def _save_experience(self, exp: ExplorationExperience):
        """保存经验"""
        experiences_file = self.storage_path / "experiences.jsonl"
        with open(experiences_file, 'a') as f:
            f.write(json.dumps(exp.to_dict(), ensure_ascii=False) + '\n')
    
    def save_snapshot(self, name: str = None):
        """保存完整快照"""
        if name is None:
            name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot_path = self.storage_path / "snapshots"
        snapshot_path.mkdir(exist_ok=True)
        
        snapshot = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_statistics(),
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": {k: v.to_dict() for k, v in self.edges.items()},
            "experiences": {k: v.to_dict() for k, v in self.experiences.items()},
        }
        
        with open(snapshot_path / f"{name}.json", 'w') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        return snapshot_path / f"{name}.json"
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_experiences": len(self.experiences),
            "by_node_type": {
                nt.name: len([n for n in self.nodes.values() if n.node_type == nt])
                for nt in NodeType
            },
            "by_edge_type": {
                et.name: len([e for e in self.edges.values() if e.edge_type == et])
                for et in EdgeType
            },
            "implications": {
                "known": len(self._implication_index),
                "proven": len([n for n in self.nodes.values() 
                               if n.node_type == NodeType.EQUATION_PAIR 
                               and n.content.get("status") == "proven"]),
                "refuted": len([n for n in self.nodes.values() 
                                if n.node_type == NodeType.EQUATION_PAIR 
                                and n.content.get("status") == "refuted"]),
            },
            "strategy_usage": {
                strategy: len(exp_ids)
                for strategy, exp_ids in self._strategy_index.items()
            },
        }


# 便捷函数
def create_knowledge_graph() -> KnowledgeGraph:
    """创建默认知识图谱"""
    return KnowledgeGraph()


if __name__ == "__main__":
    # 测试
    kg = create_knowledge_graph()
    
    # 添加方程
    kg.add_equation(65, "x = y ◇ (x ◇ y)", "Eq65")
    kg.add_equation(359, "0 = x ◇ (y ◇ (y ◇ x))", "Eq359")
    
    # 添加implication
    kg.add_implication(65, 359, status="unknown")
    
    # 记录经验
    exp = kg.record_experience(
        from_eq=65, to_eq=359,
        succeeded=False, result_type="unknown",
        strategy="SmallMagmaEnumeration",
        key_insight="No counterexample found up to order 5",
    )
    
    print(f"Knowledge Graph Statistics:")
    print(json.dumps(kg.get_statistics(), indent=2))
