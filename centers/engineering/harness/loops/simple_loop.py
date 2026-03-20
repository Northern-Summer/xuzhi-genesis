"""
简单循环 - Phase 2
参考: mini-SWE-agent Agent.simple_loop()

核心设计:
- 异常作为控制流
- 步骤/成本限制
- 可观测性
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from core.model import Model
    from core.retry import LoopConfig, LoopStats

logger = logging.getLogger("loop")


# ============================================================================
# 配置
# ============================================================================

@dataclass
class SimpleLoopConfig:
    """简单循环配置"""
    max_steps: int = 30
    max_cost: float = 10.0
    step_limit: int = 0  # 0 = 无限制
    cost_limit: float = 0.0  # 0 = 无限制
    
    def __post_init__(self):
        # 确保 step_limit 和 cost_limit 被正确应用
        self.step_limit = self.step_limit or self.max_steps
        self.cost_limit = self.cost_limit or self.max_cost


@dataclass
class SimpleLoopStats:
    """循环统计"""
    steps: int = 0
    cost: float = 0.0
    retries: int = 0
    cache_hits: int = 0
    start_time: float = field(default_factory=time.time)
    
    def record_step(self, cost: float = 0, cached: bool = False):
        self.steps += 1
        self.cost += cost
        if cached:
            self.cache_hits += 1
    
    def record_retry(self):
        self.retries += 1
    
    @property
    def duration(self) -> float:
        return time.time() - self.start_time
    
    @property
    def steps_per_second(self) -> float:
        duration = self.duration
        if duration == 0:
            return 0
        return self.steps / duration
    
    def to_dict(self) -> dict:
        return {
            "steps": self.steps,
            "cost": f"${self.cost:.6f}",
            "retries": self.retries,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": f"{self.cache_hits / max(1, self.steps) * 100:.1f}%",
            "duration": f"{self.duration:.1f}s",
            "steps_per_second": f"{self.steps_per_second:.2f}",
        }


# ============================================================================
# 异常
# ============================================================================

class LoopInterrupt(Exception):
    """循环中断基类 - 参考 InterruptAgentFlow"""
    
    def __init__(
        self,
        message: str,
        *,
        exit_status: str = "INTERRUPTED",
        submission: str = "",
    ):
        self.message = message
        self.exit_status = exit_status
        self.submission = submission
        super().__init__(message)


class TaskCompleted(LoopInterrupt):
    """任务完成"""
    
    def __init__(self, submission: str = ""):
        super().__init__(
            "Task completed successfully",
            exit_status="COMPLETED",
            submission=submission,
        )


class StepLimitExceeded(LoopInterrupt):
    """步骤超限"""
    
    def __init__(self, limit: int):
        super().__init__(
            f"Exceeded step limit ({limit})",
            exit_status="STEP_LIMIT_EXCEEDED",
        )


class CostLimitExceeded(LoopInterrupt):
    """成本超限"""
    
    def __init__(self, limit: float, actual: float):
        super().__init__(
            f"Exceeded cost limit (${limit:.4f})",
            exit_status="COST_LIMIT_EXCEEDED",
        )


class FormatError(LoopInterrupt):
    """输出格式错误 - 可恢复"""
    
    def __init__(self, error: str):
        super().__init__(
            f"Format error: {error}",
            exit_status="FORMAT_ERROR",
        )


class ExecutionError(LoopInterrupt):
    """执行错误"""
    
    def __init__(self, error: str):
        super().__init__(
            f"Execution error: {error}",
            exit_status="EXECUTION_ERROR",
        )


# ============================================================================
# 简单循环
# ============================================================================

def simple_loop(
    model: Model,
    execute_fn: Callable[[list[dict]], list[dict]],
    system_message: str,
    initial_message: str,
    config: SimpleLoopConfig,
    *,
    logger: logging.Logger | None = None,
) -> tuple[str, str, SimpleLoopStats]:
    """
    简单循环 - 重现 mini-SWE-agent Agent.simple_loop()
    
    控制流:
    ┌─────────────────────────────────────────┐
    │  1. 构建初始 messages [system, user]  │
    │  2. WHILE TRUE                          │
    │  ├─ 检查 step/cost 限制                 │
    │  ├─ model.query(messages)              │
    │  ├─ 提取 actions                       │
    │  ├─ execute_fn(actions)               │
    │  ├─ format_fn → 追加到 messages       │
    │  └─ 检查 exit 状态                     │
    │  3. RETURN (exit_status, submission)   │
    └─────────────────────────────────────────┘
    
    Returns:
        (exit_status, submission, stats)
    """
    log = logger or logging.getLogger("loop")
    stats = SimpleLoopStats()
    
    # 构建初始消息
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": initial_message},
    ]
    
    log.info(
        f"Starting simple_loop: max_steps={config.max_steps}, "
        f"max_cost=${config.max_cost:.4f}"
    )
    
    while True:
        # ─────────────────────────────────────────
        # 限制检查
        # ─────────────────────────────────────────
        if config.step_limit > 0 and stats.steps >= config.step_limit:
            log.warning(f"Step limit exceeded: {stats.steps} >= {config.step_limit}")
            raise StepLimitExceeded(config.step_limit)
        
        if config.cost_limit > 0 and stats.cost >= config.cost_limit:
            log.warning(
                f"Cost limit exceeded: ${stats.cost:.4f} >= "
                f"${config.cost_limit:.4f}"
            )
            raise CostLimitExceeded(config.cost_limit, stats.cost)
        
        # ─────────────────────────────────────────
        # Step: 查询模型
        # ─────────────────────────────────────────
        log.debug(f"Step {stats.steps + 1}: Querying model...")
        
        try:
            response = model.query(messages)
        except Exception as e:
            log.error(f"Model query failed: {e}")
            raise ExecutionError(f"Model query failed: {e}")
        
        # 记录成本
        step_cost = response.get("extra", {}).get("cost", 0.0)
        stats.record_step(step_cost)
        
        # 追加响应
        messages.append(response)
        
        # ─────────────────────────────────────────
        # 检查退出
        # ─────────────────────────────────────────
        if response.get("role") == "exit":
            exit_status = response.get("extra", {}).get("exit_status", "COMPLETED")
            submission = response.get("extra", {}).get("submission", "")
            log.info(f"Loop completed: {exit_status}")
            return exit_status, submission, stats
        
        # ─────────────────────────────────────────
        # 提取并执行动作
        # ─────────────────────────────────────────
        actions = response.get("extra", {}).get("actions", [])
        
        if not actions:
            # 无动作，注入错误让模型重新生成
            log.warning("No actions in response, injecting error...")
            error_msg = {
                "role": "user",
                "content": (
                    "Error: No tool calls found in your response. "
                    "You MUST include at least one tool call."
                ),
                "extra": {"interrupt_type": "FormatError"},
            }
            messages.append(error_msg)
            continue
        
        log.debug(f"Step {stats.steps}: Executing {len(actions)} action(s)...")
        
        try:
            outputs = execute_fn(actions)
        except Exception as e:
            log.error(f"Execution failed: {e}")
            error_msg = {
                "role": "user",
                "content": f"Execution error: {e}",
                "extra": {"interrupt_type": "ExecutionError"},
            }
            messages.append(error_msg)
            continue
        
        # ─────────────────────────────────────────
        # 格式化观察结果
        # ─────────────────────────────────────────
        observations = model.format_observation(outputs)
        messages.extend(observations)
        
        # 步骤完成
        log.debug(
            f"Step {stats.steps + 1} complete: cost=${step_cost:.6f}, "
            f"total=${stats.cost:.6f}"
        )
    
    # 不应到达这里
    return "UNKNOWN", "", stats
