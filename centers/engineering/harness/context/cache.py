"""
请求缓存 - Phase 2
核心功能: 减少重复 API 调用

缓存策略:
- Key: messages hash (content only)
- TTL: 300s (5分钟)
- 淘汰: LRU
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("cache")


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    
    @property
    def hit_rate(self) -> str:
        total = self.hits + self.misses
        if total == 0:
            return "N/A"
        return f"{self.hits / total * 100:.1f}%"
    
    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "evictions": self.evictions,
            "hit_rate": self.hit_rate,
        }


class RequestCache:
    """
    请求缓存 - 减少 API 调用次数
    
    设计原则:
    1. 相同 prompt → 直接返回缓存，不调用 API
    2. TTL 过期 → 自动淘汰
    3. LRU → 内存有限时淘汰最旧条目
    """
    
    def __init__(
        self,
        ttl: int = 300,
        max_entries: int = 500,
        content_only: bool = True,
    ):
        self.ttl = ttl
        self.max_entries = max_entries
        self.content_only = content_only
        self._cache: dict[str, tuple[float, Any]] = {}
        self._access_order: list[str] = []
        self.stats = CacheStats()
    
    def _make_key(
        self,
        messages: list[dict],
        model_name: str = "",
        extra: dict | None = None,
    ) -> str:
        """
        生成缓存 key
        
        策略: 对 messages 的 content 进行 hash
        这样相同内容不同格式的消息会命中同一缓存
        """
        if self.content_only:
            # 只 hash content，忽略 role 等元数据差异
            content_parts = [m.get("content", "") for m in messages]
        else:
            # 完整 hash
            content_parts = [json.dumps(m, sort_keys=True) for m in messages]
        
        content_hash = hashlib.sha256(
            "\n".join(content_parts).encode("utf-8")
        ).hexdigest()[:24]
        
        parts = [content_hash]
        if model_name:
            parts.append(model_name)
        if extra:
            parts.append(hashlib.md5(str(extra).encode()).hexdigest()[:8])
        
        return "|".join(parts)
    
    def get(
        self,
        messages: list[dict],
        model_name: str = "",
        **kwargs,
    ) -> Any | None:
        """获取缓存，命中返回数据，未命中返回 None"""
        key = self._make_key(messages, model_name, kwargs)
        
        if key not in self._cache:
            self.stats.misses += 1
            logger.debug(f"Cache MISS: {key[:20]}...")
            return None
        
        timestamp, cached_data = self._cache[key]
        
        # 检查 TTL
        age = time.time() - timestamp
        if age > self.ttl:
            logger.debug(f"Cache EXPIRED: {key[:20]}... (age={age:.0f}s)")
            del self._cache[key]
            self._access_order.remove(key)
            self.stats.misses += 1
            return None
        
        # LRU: 移动到末尾
        self._access_order.remove(key)
        self._access_order.append(key)
        
        self.stats.hits += 1
        logger.debug(f"Cache HIT: {key[:20]}... (age={age:.0f}s)")
        return cached_data
    
    def set(
        self,
        messages: list[dict],
        data: Any,
        model_name: str = "",
        **kwargs,
    ):
        """设置缓存"""
        key = self._make_key(messages, model_name, kwargs)
        
        # LRU 淘汰
        while len(self._cache) >= self.max_entries and self._access_order:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
            self.stats.evictions += 1
            logger.debug(f"Cache EVICT: {oldest_key[:20]}...")
        
        self._cache[key] = (time.time(), data)
        self._access_order.append(key)
        self.stats.sets += 1
        logger.debug(f"Cache SET: {key[:20]}...")
    
    def invalidate(self, messages: list[dict], model_name: str = "", **kwargs):
        """手动使缓存失效"""
        key = self._make_key(messages, model_name, kwargs)
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)
            logger.debug(f"Cache INVALIDATE: {key[:20]}...")
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Cache cleared")
    
    def prune_expired(self):
        """删除所有过期条目"""
        now = time.time()
        expired_keys = [
            k for k, (ts, _) in self._cache.items()
            if now - ts > self.ttl
        ]
        for key in expired_keys:
            del self._cache[key]
            self._access_order.remove(key)
        if expired_keys:
            logger.info(f"Pruned {len(expired_keys)} expired entries")
        return len(expired_keys)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats.to_dict(),
            "entries": len(self._cache),
            "max_entries": self.max_entries,
            "ttl": self.ttl,
        }
