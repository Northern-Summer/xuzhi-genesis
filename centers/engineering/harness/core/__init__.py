"""
Harness Core - History, Truncation, Config
==========================================
"""

from .history import (
    AbstractHistoryProcessor,
    DefaultHistoryProcessor,
    LastNObservations,
    CacheControlProcessor,
    RemoveRedundantToolCalls,
    SquashAgentReplies,
    HistoryProcessorPipeline,
    PROCESSOR_REGISTRY,
    get_history_processor,
    HistoryItem,
    History,
)

from .truncation import (
    ObservationTruncator,
    BashOutputTruncator,
    ErrorAwareTruncator,
    MultiModalTruncator,
    truncate_observation,
    TruncationResult,
)

try:
    from .config import (
        HarnessConfig,
        get_config,
        load_config,
        validate_config,
    )
except ImportError:
    # Config may not exist yet
    HarnessConfig = None
    get_config = None
    load_config = None
    validate_config = None

__all__ = [
    # History
    "AbstractHistoryProcessor",
    "DefaultHistoryProcessor",
    "LastNObservations",
    "CacheControlProcessor",
    "RemoveRedundantToolCalls",
    "SquashAgentReplies",
    "HistoryProcessorPipeline",
    "PROCESSOR_REGISTRY",
    "get_history_processor",
    "HistoryItem",
    "History",
    # Truncation
    "ObservationTruncator",
    "BashOutputTruncator",
    "ErrorAwareTruncator",
    "MultiModalTruncator",
    "truncate_observation",
    "TruncationResult",
    # Config
    "HarnessConfig",
    "get_config",
    "load_config",
    "validate_config",
]
