"""
History Processor Framework - SWE-agent inspired
==================================================
Inspired by sweagent/agent/history_processors.py

Provides pluggable history processing with truncation,
caching, and tag-based filtering.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

# Type definitions
HistoryItem = dict
History = list[HistoryItem]


class AbstractHistoryProcessor(Protocol):
    """Protocol for history processors - matches SWE-agent design"""
    
    def __call__(self, history: History) -> History:
        raise NotImplementedError


# Utility functions (from SWE-agent)
def _get_content_text(entry: HistoryItem) -> str:
    """Extract text content from a history entry"""
    if isinstance(entry.get("content"), str):
        return entry["content"]
    if isinstance(entry.get("content"), list):
        for item in entry["content"]:
            if item.get("type") == "text":
                return item["text"]
    return ""


def _get_content_stats(entry: HistoryItem) -> tuple[int, int]:
    """Get line count and image count from entry"""
    if isinstance(entry.get("content"), str):
        return len(entry["content"].splitlines()), 0
    n_text_lines = sum(
        len(item.get("text", "").splitlines())
        for item in entry.get("content", [])
        if item.get("type") == "text"
    )
    n_images = sum(
        1 for item in entry.get("content", [])
        if item.get("type") == "image_url"
    )
    return n_text_lines, n_images


def _set_cache_control(entry: HistoryItem, last_n: int | None = None) -> None:
    """Set cache_control for prompt caching (SWE-agent style)"""
    if isinstance(entry.get("content"), list):
        for item in entry["content"]:
            if item.get("type") == "text":
                item["cache_control"] = {"type": "ephemeral"}
                break
    elif entry.get("role") != "tool":
        entry["content"] = [{
            "type": "text",
            "text": _get_content_text(entry),
            "cache_control": {"type": "ephemeral"},
        }]


# =============================================================================
# History Processors
# =============================================================================

class DefaultHistoryProcessor(BaseModel):
    """
    Default processor - passes history through unchanged.
    Used as the base case.
    """
    type: Literal["default"] = "default"
    model_config = ConfigDict(extra="forbid")

    def __call__(self, history: History) -> History:
        return history


class LastNObservations(BaseModel):
    """
    Elide all but the last n observations.
    
    Inspired by SWE-agent's classic history processor used in the paper.
    Elided observations are replaced with "Old environment output: (n lines omitted)".
    
    Configuration:
        n: Number of observations to keep
        polling: Steps between updates (reduces cache invalidation)
        always_remove_tags: Observations with these tags are always elided
        always_keep_tags: Observations with these tags are never elided
    """
    n: int = 5
    """Number of recent observations to keep"""
    
    polling: int = 1
    """
    How many steps to keep between updating. This reduces prompt cache
    invalidation because we don't change history on every step.
    """
    
    always_remove_output_for_tags: set[str] = {"remove_output"}
    """Any observation with these tags will be elided even if recent"""
    
    always_keep_output_for_tags: set[str] = {"keep_output", "is_demo"}
    """Any observation with these tags will be kept even if old"""
    
    type: Literal["last_n_observations"] = "last_n_observations"
    model_config = ConfigDict(extra="forbid")

    def _get_omit_indices(self, history: History) -> list[int]:
        """Find observation indices to omit"""
        observation_indices = [
            idx for idx, entry in enumerate(history)
            if entry.get("message_type") == "observation"
            and not entry.get("is_demo", False)
        ]
        if len(observation_indices) <= self.n:
            return []
        
        # Calculate cutoff based on polling
        # Every `polling` steps, we elide one more observation
        cycle_position = len(observation_indices) // self.polling
        cutoff = max(0, cycle_position - self.n)
        
        # Never remove the first observation (instance template)
        result = observation_indices[1:cutoff] if cutoff > 0 else []
        return result

    def __call__(self, history: History) -> History:
        omit_indices = self._get_omit_indices(history)
        keep_indices = set(range(len(history))) - set(omit_indices)
        
        new_history: History = []
        for idx, entry in enumerate(history):
            tags = set(entry.get("tags", []))
            
            # Check tag-based overrides
            if tags & self.always_keep_output_for_tags:
                new_history.append(entry)
                continue
            if tags & self.always_remove_output_for_tags:
                # Replace with placeholder
                new_entry = entry.copy()
                n_lines, n_images = _get_content_stats(entry)
                placeholder = (
                    f"[{n_lines} lines of old output {'+ ' + str(n_images) + ' images' if n_images else ''} "
                    f"omitted due to history limit. "
                    f"Use tags=['keep_output'] to preserve important outputs.]"
                )
                if isinstance(new_entry.get("content"), str):
                    new_entry["content"] = placeholder
                new_history.append(new_entry)
                continue
            
            # Normal handling
            if idx in keep_indices:
                new_history.append(entry)
            elif entry.get("message_type") == "observation":
                new_entry = entry.copy()
                n_lines, n_images = _get_content_stats(entry)
                new_entry["content"] = (
                    f"[{n_lines} lines of old output omitted]"
                )
                new_history.append(new_entry)
            else:
                new_history.append(entry)
        
        return new_history


class CacheControlProcessor(BaseModel):
    """
    Enable prompt caching for the last n messages.
    
    Sets cache_control=ephemeral on recent entries to enable
    API-level prompt caching (works with Claude, GPT-4o, etc.)
    """
    last_n: int = 2
    """Number of recent messages to mark for caching"""
    
    skip_roles: set[str] = {"tool"}
    """Don't add cache control to these roles"""
    
    type: Literal["cache_control"] = "cache_control"
    model_config = ConfigDict(extra="forbid")

    def __call__(self, history: History) -> History:
        if len(history) <= self.last_n:
            return history
        
        new_history = []
        for idx, entry in enumerate(history):
            new_entry = entry.copy()
            if (
                idx >= len(history) - self.last_n
                and entry.get("role") not in self.skip_roles
            ):
                _set_cache_control(new_entry)
            new_history.append(new_entry)
        
        return new_history


class RemoveRedundantToolCalls(BaseModel):
    """
    Remove redundant consecutive tool calls to the same tool.
    
    Keeps only the last call in a sequence of calls to the same tool,
    replacing earlier ones with placeholders.
    """
    type: Literal["remove_redundant_tools"] = "remove_redundant_tools"
    model_config = ConfigDict(extra="forbid")

    def __call__(self, history: History) -> History:
        if not history:
            return history
        
        new_history = []
        last_tool = None
        for entry in history:
            current_tool = entry.get("tool", "") or entry.get("name", "")
            
            if entry.get("role") == "tool":
                if current_tool == last_tool:
                    # Replace with placeholder
                    new_entry = entry.copy()
                    new_entry["content"] = f"[Previous {current_tool} call omitted - see next]"
                    new_history.append(new_entry)
                else:
                    new_history.append(entry)
                    last_tool = current_tool
            else:
                new_history.append(entry)
                last_tool = None
        
        return new_history


class SquashAgentReplies(BaseModel):
    """
    Squash consecutive agent replies without tool intervention into single entry.
    
    This reduces context length when the agent is in a back-and-forth
    reasoning loop without executing tools.
    """
    max_consecutive: int = 3
    """Maximum consecutive agent replies before squashing"""
    
    type: Literal["squash_agent_replies"] = "squash_agent_replies"
    model_config = ConfigDict(extra="forbid")

    def __call__(self, history: History) -> History:
        if not history:
            return history
        
        new_history: History = []
        consecutive_count = 0
        
        for entry in history:
            if entry.get("role") == "assistant" and not entry.get("tool_calls"):
                consecutive_count += 1
                if consecutive_count <= self.max_consecutive:
                    new_history.append(entry)
                elif consecutive_count == self.max_consecutive + 1:
                    # Replace with summary
                    new_entry = entry.copy()
                    new_entry["content"] = (
                        f"[{self.max_consecutive} consecutive agent replies "
                        f"summarized - see later context for details]"
                    )
                    new_history.append(new_entry)
                # Skip if > max_consecutive + 1
            else:
                consecutive_count = 0
                new_history.append(entry)
        
        return new_history


# =============================================================================
# Processor Pipeline
# =============================================================================

class HistoryProcessorPipeline(BaseModel):
    """
    Chain multiple history processors together.
    
    Processors are applied in order, each receiving the output
    of the previous processor.
    """
    processors: list[DefaultHistoryProcessor | LastNObservations | CacheControlProcessor] = (
        Field(default_factory=lambda: [DefaultHistoryProcessor()])
    )
    model_config = ConfigDict(extra="forbid")

    def __call__(self, history: History) -> History:
        result = history
        for processor in self.processors:
            result = processor(result)
        return result


# =============================================================================
# Registry
# =============================================================================

PROCESSOR_REGISTRY: dict[str, type] = {
    "default": DefaultHistoryProcessor,
    "last_n_observations": LastNObservations,
    "cache_control": CacheControlProcessor,
    "remove_redundant_tools": RemoveRedundantToolCalls,
    "squash_agent_replies": SquashAgentReplies,
}


def get_history_processor(config: dict) -> AbstractHistoryProcessor:
    """Factory function to create history processor from config"""
    processor_type = config.get("type", "default")
    
    if processor_type not in PROCESSOR_REGISTRY:
        raise ValueError(
            f"Unknown processor type: {processor_type}. "
            f"Available: {list(PROCESSOR_REGISTRY.keys())}"
        )
    
    processor_class = PROCESSOR_REGISTRY[processor_type]
    return processor_class(**config)
