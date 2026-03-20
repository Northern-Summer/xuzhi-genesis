"""
Phase 2 测试
核心测试: Model 抽象层, RequestCache, simple_loop

运行: pytest tests/test_phase2.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# 导入被测试模块
import sys
sys.path.insert(0, ".")

from core.model import (
    Model, ModelConfig, RequestCache, CostStats,
    QueryTimeout, ModelUnavailable, RateLimitExceeded,
)
from core.retry import (
    LoopInterrupt, TaskCompleted, StepLimitExceeded,
    CostLimitExceeded, FormatError, RetryPolicy,
    LoopConfig, LoopStats,
)
from loops.simple_loop import SimpleLoopConfig, SimpleLoopStats
from context.cache import RequestCache as NewRequestCache, CacheStats


# ============================================================================
# Model 测试
# ============================================================================

class TestModelConfig:
    """ModelConfig 测试"""
    
    def test_default_values(self):
        config = ModelConfig(model_name="test/model")
        assert config.model_name == "test/model"
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.cache_enabled is True
    
    def test_custom_values(self):
        config = ModelConfig(
            model_name="custom/model",
            timeout=120,
            max_retries=5,
            cache_enabled=False,
        )
        assert config.timeout == 120
        assert config.max_retries == 5
        assert config.cache_enabled is False


class TestRequestCache:
    """RequestCache 测试 - 核心: 减少 API 调用"""
    
    def test_cache_miss(self):
        """未命中返回 None"""
        cache = RequestCache()
        messages = [{"role": "user", "content": "hello"}]
        result = cache.get(messages, "test/model")
        assert result is None
    
    def test_cache_hit(self):
        """命中返回缓存数据"""
        cache = RequestCache()
        messages = [{"role": "user", "content": "hello"}]
        cached_data = {"role": "assistant", "content": "hi"}
        
        cache.set(messages, cached_data, "test/model")
        result = cache.get(messages, "test/model")
        
        assert result == cached_data
    
    def test_different_messages_no_hit(self):
        """不同消息不命中"""
        cache = RequestCache()
        messages1 = [{"role": "user", "content": "hello"}]
        messages2 = [{"role": "user", "content": "world"}]
        cached_data = {"role": "assistant", "content": "hi"}
        
        cache.set(messages1, cached_data, "test/model")
        result = cache.get(messages2, "test/model")
        
        assert result is None
    
    def test_lru_eviction(self):
        """LRU 淘汰"""
        cache = RequestCache(max_entries=2)
        messages = [
            [{"role": "user", "content": f"msg{i}"}]
            for i in range(3)
        ]
        
        # 填充缓存
        for i, msg in enumerate(messages):
            cache.set(msg, {"result": i}, "test/model")
        
        # 前两个应该被淘汰
        assert cache.get(messages[0], "test/model") is None
        # LRU: max_entries=2 时，插入 3 个保留最后 2 个
        # msg1 和 msg2 保留 (msg0 被淘汰)
        assert cache.get(messages[1], "test/model") == {"result": 1}
        assert cache.get(messages[2], "test/model") == {"result": 2}
    
    def test_stats(self):
        """统计"""
        cache = RequestCache()
        messages = [{"role": "user", "content": "hello"}]
        
        cache.get(messages, "test/model")  # miss
        cache.set(messages, {"data": 1}, "test/model")
        cache.get(messages, "test/model")  # hit
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1


# ============================================================================
# Context Cache 测试
# ============================================================================

class TestContextCache:
    """新的 Context Cache 测试"""
    
    def test_cache_key_consistency(self):
        """相同内容生成相同 key"""
        cache = NewRequestCache()
        messages1 = [{"role": "user", "content": "hello"}]
        messages2 = [{"role": "user", "content": "hello"}]
        
        key1 = cache._make_key(messages1, "model")
        key2 = cache._make_key(messages2, "model")
        
        assert key1 == key2
    
    def test_content_only_hash(self):
        """content_only=True 时忽略 role"""
        cache = NewRequestCache(content_only=True)
        messages1 = [{"role": "user", "content": "hello"}]
        messages2 = [{"role": "assistant", "content": "hello"}]
        
        key1 = cache._make_key(messages1, "model")
        key2 = cache._make_key(messages2, "model")
        
        # content 相同，key 应该相同
        assert key1 == key2


# ============================================================================
# Retry 测试
# ============================================================================

class TestRetryPolicy:
    """RetryPolicy 测试"""
    
    def test_exponential_delay(self):
        """指数退避"""
        policy = RetryPolicy(initial_delay=1.0, exponential_base=2.0, jitter=False)
        
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0
    
    def test_max_delay(self):
        """最大延迟限制"""
        policy = RetryPolicy(initial_delay=1.0, max_delay=5.0, jitter=False)
        
        assert policy.get_delay(10) == 5.0


class TestLoopExceptions:
    """循环异常测试"""
    
    def test_task_completed(self):
        """TaskCompleted 异常"""
        exc = TaskCompleted("submission content")
        assert exc.exit_status == "COMPLETED"
        assert exc.submission == "submission content"
    
    def test_step_limit_exceeded(self):
        """StepLimitExceeded 异常"""
        exc = StepLimitExceeded(30)
        assert exc.exit_status == "STEP_LIMIT_EXCEEDED"
        assert "30" in exc.message
    
    def test_cost_limit_exceeded(self):
        """CostLimitExceeded 异常"""
        exc = CostLimitExceeded(10.0, 15.0)
        assert exc.exit_status == "COST_LIMIT_EXCEEDED"
    
    def test_format_error(self):
        """FormatError 异常"""
        exc = FormatError("No tool calls found")
        assert exc.exit_status == "FORMAT_ERROR"


class TestSimpleLoopStats:
    """SimpleLoopStats 测试"""
    
    def test_record_step(self):
        """记录步骤"""
        stats = SimpleLoopStats()
        stats.record_step(cost=0.5)
        
        assert stats.steps == 1
        assert stats.cost == 0.5
    
    def test_cache_hit_tracking(self):
        """缓存命中跟踪"""
        stats = SimpleLoopStats()
        stats.record_step(cost=0, cached=True)
        stats.record_step(cost=0.5, cached=False)
        
        assert stats.cache_hits == 1
    
    def test_duration(self):
        """时长计算"""
        import time
        stats = SimpleLoopStats()
        time.sleep(0.01)
        assert stats.duration > 0
    
    def test_to_dict(self):
        """转换为字典"""
        stats = SimpleLoopStats()
        stats.record_step(cost=0.5)
        
        d = stats.to_dict()
        assert d["steps"] == 1
        assert d["cost"] == "$0.500000"
        assert "duration" in d


# ============================================================================
# SimpleLoopConfig 测试
# ============================================================================

class TestSimpleLoopConfig:
    """SimpleLoopConfig 测试"""
    
    def test_default_values(self):
        """默认值"""
        config = SimpleLoopConfig()
        assert config.max_steps == 30
        assert config.max_cost == 10.0
    
    def test_step_limit_override(self):
        """step_limit 覆盖"""
        config = SimpleLoopConfig(step_limit=10)
        assert config.step_limit == 10
        assert config.max_steps == 30  # 未被修改
    
    def test_cost_limit_override(self):
        """cost_limit 覆盖"""
        config = SimpleLoopConfig(cost_limit=5.0)
        assert config.cost_limit == 5.0


# ============================================================================
# Mock Model 测试
# ============================================================================

class MockModel(Model):
    """用于测试的 Mock 模型"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.call_count = 0
        self.responses = []
    
    def set_responses(self, responses: list):
        """设置响应序列"""
        self.responses = responses
    
    def _query_impl(self, messages: list[dict]) -> dict:
        """返回预设响应"""
        if self.responses:
            return self.responses.pop(0)
        return {
            "role": "assistant",
            "content": "default response",
            "extra": {"actions": [], "cost": 0.001},
        }
    
    def format_message(self, **kwargs) -> dict:
        return {"role": kwargs.get("role", "user"), "content": kwargs.get("content", "")}
    
    def format_observation(self, outputs: list[dict], **kwargs) -> list[dict]:
        return [
            {"role": "tool", "content": out.get("output", ""), "tool_call_id": f"id_{i}"}
            for i, out in enumerate(outputs)
        ]


class TestMockModel:
    """Mock Model 测试"""
    
    def test_cache_integration(self):
        """缓存集成"""
        config = ModelConfig(model_name="mock/model", cache_enabled=True)
        model = MockModel(config)
        
        messages = [{"role": "user", "content": "test"}]
        model.set_responses([{"role": "assistant", "content": "response", "extra": {"actions": [], "cost": 0.001}}])
        
        # 第一次调用
        r1 = model.query(messages)
        assert r1["content"] == "response"
        assert model.cost_stats.total_requests == 1
        
        # 第二次调用应该命中缓存
        r2 = model.query(messages)
        assert r2["content"] == "response"
        assert model.cost_stats.cache_hits == 1


# ============================================================================
# 运行
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
