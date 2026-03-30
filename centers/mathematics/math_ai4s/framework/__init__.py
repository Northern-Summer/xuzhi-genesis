"""
MathAI4S Research Framework
数学AI4S研究框架

一个严谨、优雅、自维护的数学研究工具框架。
遵循五条铁律，支持多种探索策略。

Components:
    - core_architecture: 核心数据结构和类型
    - exploration_strategies: 数学探索策略
    - verification_layer: 验证和证明检查
    - self_maintenance: 自维护系统
    - main: 命令行入口

Usage:
    from framework import ResearchSession, StrategyOrchestrator
    
    session = ResearchSession(session_id="test", target_implications=[(65, 359)])
    orchestrator = StrategyOrchestrator()
    result = orchestrator.explore(65, 359)

Author: Δ (Delta-Forge)
Version: 1.0.0
Date: 2026-03-30
"""

__version__ = "1.0.0"
__author__ = "Δ (Delta-Forge)"

from .core_architecture import (
    Magma,
    EquationalLaw,
    ImplicationResult,
    ResearchSession,
    ProofStatus,
    VerificationLevel,
    FiveRulesChecker,
)

from .exploration_strategies import (
    ExplorationStrategy,
    SmallMagmaEnumeration,
    LinearModelStrategy,
    SymmetryReductionStrategy,
    StrategyOrchestrator,
)

from .verification_layer import (
    VampireProver,
    Mace4Finder,
    LeanVerifier,
    VerificationPipeline,
)

from .self_maintenance import (
    SelfMaintenance,
    FileJanitor,
    IntegrityChecker,
    BackupManager,
)

__all__ = [
    # Core
    "Magma",
    "EquationalLaw",
    "ImplicationResult",
    "ResearchSession",
    "ProofStatus",
    "VerificationLevel",
    "FiveRulesChecker",
    # Strategies
    "ExplorationStrategy",
    "SmallMagmaEnumeration",
    "LinearModelStrategy",
    "SymmetryReductionStrategy",
    "StrategyOrchestrator",
    # Verification
    "VampireProver",
    "Mace4Finder",
    "LeanVerifier",
    "VerificationPipeline",
    # Maintenance
    "SelfMaintenance",
    "FileJanitor",
    "IntegrityChecker",
    "BackupManager",
]
