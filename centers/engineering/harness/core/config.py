#!/usr/bin/env python3
"""
Harness Engineering - Core Configuration
=========================================
Manages harness-wide configuration with validation and defaults.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

class HarnessConfig:
    """Harness configuration manager with validation."""
    
    DEFAULT_CONFIG = {
        "harness_version": "1.0.0",
        "context": {
            "max_tokens": 128000,  # Leave 4K for response
            "reserve_tokens": 4096,
            "compression_threshold": 0.85,
            "checkpoint_interval": 50,  # Checkpoint every N turns
        },
        "tools": {
            "enabled": True,
            "safety_mode": "strict",  # strict, moderate, permissive
            "denylist": ["format:disk", "format:format", "exec:rm -rf"],
            "timeout_seconds": 30,
        },
        "history": {
            "compression": "semantic",  # semantic, token, none
            "max_sessions": 10,
            "checkpoint_enabled": True,
            "handoff_preservation": True,
        },
        "guards": {
            "error_threshold": 3,  # Max consecutive errors before circuit break
            "retry_attempts": 2,
            "circuit_breaker_timeout": 60,
            "rate_limit_backoff": 1.5,
        },
        "routing": {
            "strategy": "capability",  # capability, latency, cost, mixed
            "preferred_provider": "accelerator",
            "fallback_chain": ["accelerator", "ollama"],
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._default_config_path()
        self.config = self._load()
        
    def _default_config_path(self) -> Path:
        return Path.home() / "xuzhi_genesis" / "centers" / "engineering" / "harness" / "config.json"
    
    def _load(self) -> Dict[str, Any]:
        """Load configuration with defaults fallback."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    user_config = json.load(f)
                return self._merge_config(self.DEFAULT_CONFIG, user_config)
            except (json.JSONDecodeError, Exception) as e:
                print(f"[HARNESS] Config load error: {e}, using defaults", file=__import__('sys').stderr)
        return self.DEFAULT_CONFIG.copy()
    
    def _merge_config(self, defaults: Dict, user: Dict) -> Dict:
        """Deep merge user config into defaults."""
        result = defaults.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set config value by dot-notation key."""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save configuration to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration and return (is_valid, errors)."""
        errors = []
        
        # Context validation
        ctx = self.config.get("context", {})
        if ctx.get("max_tokens", 0) < 10000:
            errors.append("context.max_tokens must be >= 10000")
        if ctx.get("reserve_tokens", 0) < 1000:
            errors.append("context.reserve_tokens must be >= 1000")
            
        # Tools validation
        tools = self.config.get("tools", {})
        if tools.get("safety_mode") not in ["strict", "moderate", "permissive"]:
            errors.append("tools.safety_mode must be strict|moderate|permissive")
            
        # Guards validation
        guards = self.config.get("guards", {})
        if guards.get("error_threshold", 0) < 1:
            errors.append("guards.error_threshold must be >= 1")
            
        return (len(errors) == 0, errors)


# Singleton instance
_config_instance: Optional[HarnessConfig] = None

def get_config() -> HarnessConfig:
    """Get singleton harness config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = HarnessConfig()
    return _config_instance


if __name__ == "__main__":
    config = get_config()
    valid, errors = config.validate()
    print(f"Harness Config v{config.get('harness_version')}")
    print(f"Valid: {valid}")
    if not valid:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print(f"Context: {config.get('context.max_tokens')} tokens max")
        print(f"Safety: {config.get('tools.safety_mode')} mode")
        print(f"Routing: {config.get('routing.strategy')} strategy")
