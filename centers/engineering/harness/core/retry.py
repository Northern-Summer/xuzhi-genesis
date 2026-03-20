"""
重试循环 - Phase 2
参考: mini-SWE-agent InterruptAgentFlow

核心设计:
- 异常作为控制流
- 指数退避重试
- 分层错误处理
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

import tenacity

logger = logging.getLogger("retry")

T = TypeVar("T")


# ============================================================================
# 异常体系
# ============================================================================

class LoopInterrupt(Exception):
    """循环中断基类 - 参考 InterruptAgentFlow"""
    
    def __init__(self, message: str, *, exit_status: str = "", submission: str = ""):
        self.message = message
        self.exit_status = exit_status
        self.submission = submission
        super().__init__(message)


class TaskCompleted(LoopInterrupt):
    """任务完成"""
    
    def __init__(self, submission: str):
        super().__init__(
            "Task completed successfully",
            exit_status="COMPLETED",
            submission=submission
        )


class StepLimitExceeded(LoopInterrupt):
    """步骤超限"""
    
    def __init__(self, limit: int):
        super().__init__(
            f"Exceeded step limit ({limit})",
            exit_status="STEP_LIMIT_EXCEEDED"
        )


class CostLimitExceeded(LoopInterrupt):
    """成本超限"""
    
    def __init__(self, limit: float, actual: float):
        super().__init__(
            f"Exceeded cost limit (${limit:.4f} > ${actual:.4f})",
            exit_status="COST_LIMIT_EXCEEDED"
        )


class FormatError(LoopInterrupt):
    """输出格式错误 - 可恢复"""
    
    def __init__(self, error: str):
        super().__init__(
            f"Format error: {error}",
            exit_status="FORMAT_ERROR"
        )


class ExecutionError(LoopInterrupt):
    """执行错误"""
    
    def __init__(self, error: str):
        super().__init__(
            f"Execution error: {error}",
            exit_status="EXECUTION_ERROR"
        )


# ============================================================================
# 错误分类
# ============================================================================

class ErrorSeverity(Enum):
    """错误严重程度"""
    RECOVERABLE = "recoverable"      # 可恢复，重试
    RETRYABLE = "retryable"          # 可重试，有次数限制
    FATAL = "fatal"                  # 致命，终止


@dataclass
class ErrorInfo:
    """错误信息"""
    error: Exception
    severity: ErrorSeverity
    retry_count: int = 0
    timestamp: float = field(default_factory=time.time)
    
    @property
    def should_retry(self) -> bool:
        return self.severity in (ErrorSeverity.RECOVERABLE, ErrorSeverity.RETRYABLE)
    
    @property
    def should_abort(self) -> bool:
        return self.severity == ErrorSeverity.FATAL


def classify_error(error: Exception) -> ErrorInfo:
    """分类错误并返回错误信息"""
    
    # 可恢复错误
    recoverable_errors = (
        tenacity.RetryError,
    )
    
    # 可重试错误
    retryable_errors = (
        TimeoutError,
        ConnectionError,
        OSError,
    )
    
    # 致命错误
    fatal_errors = (
        KeyboardInterrupt,
        SystemExit,
    )
    
    if isinstance(error, recoverable_errors):
        return ErrorInfo(error, ErrorSeverity.RECOVERABLE)
    elif isinstance(error, retryable_errors):
        return ErrorInfo(error, ErrorSeverity.RETRYABLE)
    elif isinstance(error, fatal_errors):
        return ErrorInfo(error, ErrorSeverity.FATAL)
    else:
        # 默认按可重试处理
        return ErrorInfo(error, ErrorSeverity.RETRYABLE)


# ============================================================================
# 重试策略
# ============================================================================

@dataclass
class RetryPolicy:
    """重试策略配置"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def get_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            import random
            delay *= (0.5 + random.random())  # 50%-150%
        return delay


# ============================================================================
# 简单循环
# ============================================================================

@dataclass
class LoopConfig:
    """循环配置"""
    max_steps: int = 30
    max_cost: float = 10.0
    step_limit: int = 0
    cost_limit: float = 0.0
    
    
@dataclass
class LoopStats:
    """循环统计"""
    steps: int = 0
    cost: float = 0.0
    retries: int = 0
    start_time: float = field(default_factory=time.time)
    errors: list[ErrorInfo] = field(default_factory=list)
    
    def record_step(self, cost: float = 0):
        self.steps += 1
        self.cost += cost
    
    def record_retry(self):
        self.retries += 1
    
    def record_error(self, error: Exception):
        self.errors.append(classify_error(error))
    
    @property
    def duration(self) -> float:
        return time.time() - self.start_time
    
    def to_dict(self) -> dict:
        return {
            "steps": self.steps,
            "cost": f"${self.cost:.6f}",
            "retries": self.retries,
            "duration": f"{self.duration:.1f}s",
            "errors": len(self.errors),
        }


def simple_loop(
    query_fn: Callable[[list[dict]], dict],
    execute_fn: Callable[[list[dict]], list[dict]],
    format_fn: Callable[[dict, list[dict]], list[dict]],
    initial_messages: list[dict],
    config: LoopConfig,
    *,
    logger: logging.Logger | None = None,
) -> tuple[str, str, LoopStats]:
    """
    简单循环 - 参考 mini-SWE-agent Agent.simple_loop()
    
    控制流:
    1. query_fn(messages) → 模型响应
    2. execute_fn(actions) → 执行结果
    3. format_fn(response, outputs) → 观察消息
    4. 追加到 messages，重复
    
    终止条件:
    - 模型返回 exit 消息
    - 步骤超限
    - 成本超限
    
    Returns:
        (exit_status, submission, stats)
    """
    log = logger or logging.getLogger("loop")
    stats = LoopStats()
    messages = list(initial_messages)  # 复制
    
    while True:
        # 检查限制
        if config.step_limit > 0 and stats.steps >= config.step_limit:
            raise StepLimitExceeded(config.step_limit)
        
        if config.cost_limit > 0 and stats.cost >= config.cost_limit:
            raise CostLimitExceeded(config.cost_limit, stats.cost)
        
        try:
            # Step 1: 查询模型
            log.debug(f"Step {stats.steps + 1}: Querying model...")
            response = query_fn(messages)
            
            # 提取成本
            step_cost = response.get("extra", {}).get("cost", 0.0)
            stats.record_step(step_cost)
            
            # 检查退出
            if response.get("role") == "exit":
                exit_status = response.get("extra", {}).get("exit_status", "COMPLETED")
                submission = response.get("extra", {}).get("submission", "")
                return exit_status, submission, stats
            
            # 提取动作
            actions = response.get("extra", {}).get("actions", [])
            if not actions:
                # 无动作，继续循环
                log.warning("No actions in response, continuing...")
                messages.append(response)
                continue
            
            messages.append(response)
            
            # Step 2: 执行动作
            log.debug(f"Step {stats.steps}: Executing {len(actions)} action(s)...")
            outputs = execute_fn(actions)
            
            # Step 3: 格式化观察结果
            observations = format_fn(response, outputs)
            messages.extend(observations)
            
        except LoopInterrupt as e:
            log.info(f"Loop interrupted: {e.exit_status}")
            return e.exit_status, e.submission, stats
        
        except FormatError as e:
            # 格式错误，注入错误消息让模型重新生成
            log.warning(f"Format error, injecting error message: {e}")
            error_msg = {
                "role": "user",
                "content": f"Format error: {e.message}. Please respond with proper tool calls.",
                "extra": {"interrupt_type": "FormatError"}
            }
            messages.append(error_msg)
            stats.record_retry()
            
        except Exception as e:
            error_info = classify_error(e)
            stats.record_error(e)
            
            if error_info.should_abort:
                log.error(f"Fatal error, aborting: {e}")
                return "FATAL_ERROR", str(e), stats
            
            if error_info.should_retry and stats.retries < 3:
                delay = RetryPolicy().get_delay(stats.retries)
                log.warning(f"Retryable error, retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
                stats.record_retry()
            else:
                log.error(f"Error after {stats.retries} retries: {e}")
                return "ERROR", str(e), stats
    
    # 不应到达这里
    return "UNKNOWN", "", stats
