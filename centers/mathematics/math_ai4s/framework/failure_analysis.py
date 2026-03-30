#!/usr/bin/env python3
"""
FailureAnalysis — Learning from Failures
失败分析 —— 从失败中学习

设计哲学：
- 失败不是终点，而是信息的来源
- 系统性地记录、分类、分析失败
- 将失败模式转化为未来探索的指导

Author: Δ (Delta-Forge)
Date: 2026-03-30
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
import json
import hashlib


class FailureType(Enum):
    """失败类型分类"""
    # 资源限制
    TIMEOUT = auto()           # 计算超时
    MEMORY_LIMIT = auto()      # 内存不足
    EFFORT_EXHAUSTED = auto()  # 计算努力耗尽
    
    # 理论限制
    THEORETICALLY_HARD = auto()     # 理论上困难（如高阶同构问题）
    UNDECIDABLE = auto()            # 不可判定
    INCOMPLETE_THEORY = auto()      # 理论不完整
    
    # 工具限制
    ATP_FAILURE = auto()       # ATP工具失败
    LEAN_COMPILATION_ERROR = auto()  # Lean编译错误
    MODEL_SEARCH_INCOMPLETE = auto() # 模型搜索不完全
    
    # 实现问题
    BUG = auto()               # 实现bug
    CONFIGURATION_ERROR = auto()  # 配置错误
    PARSING_ERROR = auto()     # 解析错误
    
    # 外部依赖
    NETWORK_ERROR = auto()     # 网络问题
    FILE_SYSTEM_ERROR = auto() # 文件系统错误
    
    # 未知
    UNKNOWN = auto()


class RecoveryStrategy(Enum):
    """恢复策略"""
    INCREASE_EFFORT = auto()       # 增加计算努力
    REDUCE_PROBLEM_SIZE = auto()   # 减小问题规模
    SWITCH_STRATEGY = auto()       # 切换探索策略
    DECOMPOSE = auto()             # 分解问题
    APPROXIMATE = auto()           # 使用近似方法
    MANUAL_INTERVENTION = auto()   # 需要人工介入
    ABANDON = auto()               # 放弃（标记为UNKNOWN）


@dataclass
class FailureRecord:
    """失败记录"""
    # 标识
    failure_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 问题上下文
    from_eq: int
    to_eq: int
    strategy_used: str
    
    # 失败信息
    failure_type: FailureType
    failure_message: str
    stack_trace: Optional[str] = None
    
    # 资源使用
    effort_spent: int = 0           # 已花费的计算努力
    time_elapsed_seconds: float = 0.0
    memory_used_mb: float = 0.0
    
    # 恢复尝试
    recovery_attempted: List[RecoveryStrategy] = field(default_factory=list)
    recovery_successful: bool = False
    
    # 模式识别
    pattern_signature: str = ""      # 用于聚类相似失败
    related_failures: List[str] = field(default_factory=list)  # 相关失败ID
    
    # 元数据
    session_id: str = ""
    notes: List[str] = field(default_factory=list)
    
    def compute_signature(self) -> str:
        """计算失败模式签名，用于聚类"""
        sig_data = {
            "type": self.failure_type.name,
            "strategy": self.strategy_used,
            "from_eq": self.from_eq,
            "to_eq": self.to_eq,
        }
        sig_str = json.dumps(sig_data, sort_keys=True)
        return hashlib.sha256(sig_str.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "failure_id": self.failure_id,
            "timestamp": self.timestamp,
            "from_eq": self.from_eq,
            "to_eq": self.to_eq,
            "strategy_used": self.strategy_used,
            "failure_type": self.failure_type.name,
            "failure_message": self.failure_message,
            "stack_trace": self.stack_trace,
            "effort_spent": self.effort_spent,
            "time_elapsed_seconds": self.time_elapsed_seconds,
            "memory_used_mb": self.memory_used_mb,
            "recovery_attempted": [r.name for r in self.recovery_attempted],
            "recovery_successful": self.recovery_successful,
            "pattern_signature": self.pattern_signature or self.compute_signature(),
            "related_failures": self.related_failures,
            "session_id": self.session_id,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FailureRecord":
        """从字典反序列化"""
        return cls(
            failure_id=data["failure_id"],
            timestamp=data["timestamp"],
            from_eq=data["from_eq"],
            to_eq=data["to_eq"],
            strategy_used=data["strategy_used"],
            failure_type=FailureType[data["failure_type"]],
            failure_message=data["failure_message"],
            stack_trace=data.get("stack_trace"),
            effort_spent=data.get("effort_spent", 0),
            time_elapsed_seconds=data.get("time_elapsed_seconds", 0.0),
            memory_used_mb=data.get("memory_used_mb", 0.0),
            recovery_attempted=[RecoveryStrategy[r] for r in data.get("recovery_attempted", [])],
            recovery_successful=data.get("recovery_successful", False),
            pattern_signature=data.get("pattern_signature", ""),
            related_failures=data.get("related_failures", []),
            session_id=data.get("session_id", ""),
            notes=data.get("notes", []),
        )


@dataclass
class FailurePattern:
    """失败模式（聚类结果）"""
    pattern_id: str
    signature: str
    failure_type: FailureType
    
    # 统计
    occurrence_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    
    # 影响范围
    affected_equations: Set[int] = field(default_factory=set)
    affected_strategies: Set[str] = field(default_factory=set)
    
    # 恢复成功率
    recovery_attempts: int = 0
    recovery_successes: int = 0
    
    # 建议
    recommended_recovery: Optional[RecoveryStrategy] = None
    recommended_prevention: List[str] = field(default_factory=list)
    
    @property
    def recovery_success_rate(self) -> float:
        """恢复成功率"""
        if self.recovery_attempts == 0:
            return 0.0
        return self.recovery_successes / self.recovery_attempts
    
    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "signature": self.signature,
            "failure_type": self.failure_type.name,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "affected_equations": list(self.affected_equations),
            "affected_strategies": list(self.affected_strategies),
            "recovery_attempts": self.recovery_attempts,
            "recovery_successes": self.recovery_successes,
            "recovery_success_rate": self.recovery_success_rate,
            "recommended_recovery": self.recommended_recovery.name if self.recommended_recovery else None,
            "recommended_prevention": self.recommended_prevention,
        }


class FailureAnalyzer:
    """失败分析器主类"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化失败分析器
        
        Args:
            storage_path: 失败记录存储路径
        """
        if storage_path is None:
            storage_path = Path.home() / ".xuzhi_memory" / "agents" / "delta" / "failure_records"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.records: Dict[str, FailureRecord] = {}
        self.patterns: Dict[str, FailurePattern] = {}
        
        self._load_records()
    
    def _load_records(self):
        """从磁盘加载历史记录"""
        records_file = self.storage_path / "failures.jsonl"
        if records_file.exists():
            with open(records_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            record = FailureRecord.from_dict(data)
                            self.records[record.failure_id] = record
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Failed to load failure record: {e}")
        
        # 加载模式
        patterns_file = self.storage_path / "patterns.json"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                patterns_data = json.load(f)
                for p_data in patterns_data.get("patterns", []):
                    pattern = FailurePattern(
                        pattern_id=p_data["pattern_id"],
                        signature=p_data["signature"],
                        failure_type=FailureType[p_data["failure_type"]],
                        occurrence_count=p_data["occurrence_count"],
                        first_seen=p_data["first_seen"],
                        last_seen=p_data["last_seen"],
                        affected_equations=set(p_data["affected_equations"]),
                        affected_strategies=set(p_data["affected_strategies"]),
                        recovery_attempts=p_data["recovery_attempts"],
                        recovery_successes=p_data["recovery_successes"],
                        recommended_recovery=RecoveryStrategy[p_data["recommended_recovery"]] if p_data.get("recommended_recovery") else None,
                        recommended_prevention=p_data.get("recommended_prevention", []),
                    )
                    self.patterns[pattern.signature] = pattern
    
    def record_failure(self, 
                       from_eq: int, 
                       to_eq: int, 
                       strategy: str,
                       failure_type: FailureType,
                       message: str,
                       effort_spent: int = 0,
                       time_elapsed: float = 0.0,
                       memory_used: float = 0.0,
                       stack_trace: Optional[str] = None,
                       session_id: str = "") -> FailureRecord:
        """
        记录一次失败
        
        Returns:
            FailureRecord: 创建的失败记录
        """
        failure_id = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}_{from_eq}_{to_eq}"
        
        record = FailureRecord(
            failure_id=failure_id,
            from_eq=from_eq,
            to_eq=to_eq,
            strategy_used=strategy,
            failure_type=failure_type,
            failure_message=message,
            effort_spent=effort_spent,
            time_elapsed_seconds=time_elapsed,
            memory_used_mb=memory_used,
            stack_trace=stack_trace,
            session_id=session_id,
        )
        
        # 计算签名并关联模式
        signature = record.compute_signature()
        record.pattern_signature = signature
        
        # 查找相关失败
        for existing_record in self.records.values():
            if existing_record.pattern_signature == signature:
                record.related_failures.append(existing_record.failure_id)
                existing_record.related_failures.append(failure_id)
        
        self.records[failure_id] = record
        self._update_pattern(record)
        self._save_record(record)
        
        return record
    
    def _update_pattern(self, record: FailureRecord):
        """更新失败模式统计"""
        signature = record.pattern_signature
        
        if signature not in self.patterns:
            self.patterns[signature] = FailurePattern(
                pattern_id=f"P{signature}",
                signature=signature,
                failure_type=record.failure_type,
                first_seen=record.timestamp,
            )
        
        pattern = self.patterns[signature]
        pattern.occurrence_count += 1
        pattern.last_seen = record.timestamp
        pattern.affected_equations.add(record.from_eq)
        pattern.affected_equations.add(record.to_eq)
        pattern.affected_strategies.add(record.strategy_used)
        
        if record.recovery_attempted:
            pattern.recovery_attempts += len(record.recovery_attempted)
            if record.recovery_successful:
                pattern.recovery_successes += 1
        
        # 更新推荐恢复策略
        self._update_recommended_recovery(pattern)
    
    def _update_recommended_recovery(self, pattern: FailurePattern):
        """基于历史成功率更新推荐的恢复策略"""
        # 简单启发式：根据失败类型推荐
        recovery_stats: Dict[RecoveryStrategy, List[bool]] = defaultdict(list)
        
        for record in self.records.values():
            if record.pattern_signature == pattern.signature:
                for strategy in record.recovery_attempted:
                    recovery_stats[strategy].append(record.recovery_successful)
        
        if recovery_stats:
            best_strategy = max(
                recovery_stats.keys(),
                key=lambda s: sum(recovery_stats[s]) / len(recovery_stats[s]) if recovery_stats[s] else 0
            )
            pattern.recommended_recovery = best_strategy
    
    def _save_record(self, record: FailureRecord):
        """保存单个记录到磁盘"""
        records_file = self.storage_path / "failures.jsonl"
        with open(records_file, 'a') as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')
        
        # 同时更新模式文件
        self._save_patterns()
    
    def _save_patterns(self):
        """保存模式统计到磁盘"""
        patterns_file = self.storage_path / "patterns.json"
        patterns_data = {
            "patterns": [p.to_dict() for p in self.patterns.values()],
            "total_records": len(self.records),
            "last_updated": datetime.now().isoformat(),
        }
        with open(patterns_file, 'w') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)
    
    def get_pattern_for_equation(self, eq_id: int) -> List[FailurePattern]:
        """获取影响特定方程的所有失败模式"""
        return [
            p for p in self.patterns.values()
            if eq_id in p.affected_equations
        ]
    
    def get_recovery_recommendation(self, 
                                    from_eq: int, 
                                    to_eq: int, 
                                    strategy: str) -> Optional[RecoveryStrategy]:
        """
        获取针对特定问题的恢复建议
        
        基于历史相似问题的恢复成功率
        """
        # 查找匹配的模式
        best_pattern = None
        best_match_score = 0
        
        for pattern in self.patterns.values():
            score = 0
            if from_eq in pattern.affected_equations:
                score += 2
            if to_eq in pattern.affected_equations:
                score += 2
            if strategy in pattern.affected_strategies:
                score += 1
            
            if score > best_match_score:
                best_match_score = score
                best_pattern = pattern
        
        if best_pattern and best_pattern.recommended_recovery:
            return best_pattern.recommended_recovery
        
        # 默认建议
        return RecoveryStrategy.SWITCH_STRATEGY
    
    def generate_failure_report(self) -> Dict:
        """生成失败分析报告"""
        return {
            "total_failures": len(self.records),
            "unique_patterns": len(self.patterns),
            "by_type": {
                ft.name: len([r for r in self.records.values() if r.failure_type == ft])
                for ft in FailureType
            },
            "by_strategy": {
                strategy: len([r for r in self.records.values() if r.strategy_used == strategy])
                for strategy in set(r.strategy_used for r in self.records.values())
            },
            "recovery_success_rate": (
                sum(1 for r in self.records.values() if r.recovery_successful) / len(self.records)
                if self.records else 0.0
            ),
            "top_patterns": sorted(
                [p.to_dict() for p in self.patterns.values()],
                key=lambda x: x["occurrence_count"],
                reverse=True
            )[:10],
        }
    
    def mark_recovery_attempt(self, 
                              failure_id: str, 
                              strategy: RecoveryStrategy,
                              successful: bool):
        """标记对某次失败的恢复尝试"""
        if failure_id in self.records:
            record = self.records[failure_id]
            record.recovery_attempted.append(strategy)
            if successful:
                record.recovery_successful = True
            
            # 更新模式统计
            self._update_pattern(record)
            self._save_patterns()


# 便捷函数
def create_failure_analyzer() -> FailureAnalyzer:
    """创建默认配置的失败分析器"""
    return FailureAnalyzer()


if __name__ == "__main__":
    # 测试代码
    analyzer = create_failure_analyzer()
    
    # 模拟一次失败
    record = analyzer.record_failure(
        from_eq=65,
        to_eq=359,
        strategy="SmallMagmaEnumeration",
        failure_type=FailureType.EFFORT_EXHAUSTED,
        message="Exhausted all magmas up to order 5 without finding counterexample",
        effort_spent=100000,
        time_elapsed=300.0,
    )
    
    print(f"Recorded failure: {record.failure_id}")
    print(f"Pattern signature: {record.pattern_signature}")
    
    report = analyzer.generate_failure_report()
    print(f"\nFailure Report:")
    print(f"  Total failures: {report['total_failures']}")
    print(f"  Unique patterns: {report['unique_patterns']}")
