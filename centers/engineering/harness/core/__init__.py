"""
Harness Core - Phase 2
核心模块: Model, Retry, History, Truncation, Guards
"""

from core.history import (
    AbstractHistoryProcessor,
    LastNObservations,
    CacheControlProcessor,
    RemoveRedundantToolCalls,
    SquashAgentReplies,
    HistoryProcessorPipeline,
    get_history_processor,
)

from core.truncation import (
    ObservationTruncator,
    BashOutputTruncator,
    ErrorAwareTruncator,
    MultiModalTruncator,
    truncate_observation,
)

from core.model import (
    Model,
    ModelConfig,
    ModelInterrupt,
    QueryTimeout,
    ModelUnavailable,
    RateLimitExceeded,
    RequestCache,
    CostStats,
)

from core.retry import (
    LoopInterrupt,
    TaskCompleted,
    StepLimitExceeded,
    CostLimitExceeded,
    FormatError,
    ExecutionError,
    ErrorSeverity,
    ErrorInfo,
    RetryPolicy,
    LoopConfig,
    LoopStats,
    simple_loop,
)

from loops.simple_loop import (
    SimpleLoopConfig,
    SimpleLoopStats,
)

__all__ = [
    # History
    "AbstractHistoryProcessor",
    "LastNObservations",
    "CacheControlProcessor",
    "RemoveRedundantToolCalls",
    "SquashAgentReplies",
    "HistoryProcessorPipeline",
    "get_history_processor",
    # Truncation
    "ObservationTruncator",
    "BashOutputTruncator",
    "ErrorAwareTruncator",
    "MultiModalTruncator",
    "truncate_observation",
    # Model
    "Model",
    "ModelConfig",
    "ModelInterrupt",
    "QueryTimeout",
    "ModelUnavailable",
    "RateLimitExceeded",
    "RequestCache",
    "CostStats",
    # Retry
    "LoopInterrupt",
    "TaskCompleted",
    "StepLimitExceeded",
    "CostLimitExceeded",
    "FormatError",
    "ExecutionError",
    "RetryPolicy",
    "SimpleLoopConfig",
    "SimpleLoopStats",
    "simple_loop",
]
