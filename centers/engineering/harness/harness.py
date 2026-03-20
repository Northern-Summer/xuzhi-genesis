#!/usr/bin/env python3
"""
Harness Engineering - Main Entry Point
========================================
Complete harness system for LLM execution environment.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add harness to path
HARNESS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HARNESS_DIR))

from core.config import get_config, HarnessConfig
from core.context import ContextManager
from guards.guards import get_guard, GuardRail, SafetyChecker
from scaffolding.scaffold import Scaffold
from tools.registry import get_registry, register_builtin_tools

class Harness:
    """
    Main harness class that orchestrates all components.
    
    This is the complete execution environment for the LLM:
    - Configuration management
    - Context/history management
    - Safety guards and error handling
    - Scaffolding for session handoff
    - Tool registry
    """
    
    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.home() / "xuzhi_genesis" / "centers" / "engineering" / "harness"
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.config = get_config()
        self.context = ContextManager(
            max_tokens=self.config.get("context.max_tokens", 128000),
            reserve_tokens=self.config.get("context.reserve_tokens", 4096),
            compression_threshold=self.config.get("context.compression_threshold", 0.85),
            checkpoint_dir=self.workspace / "history"
        )
        self.guard = get_guard()
        self.scaffold = Scaffold(workspace=self.workspace)
        self.tools = get_registry()
        
        # Register built-in tools
        register_builtin_tools()
        
        # State
        self.initialized_at = time.time()
        self.is_active = True
        
    def run(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task through the harness.
        
        Args:
            task: Task description or name
            **kwargs: Additional parameters
            
        Returns:
            Dict with success, result, and metadata
        """
        start_time = time.time()
        
        # Start turn in context
        self.context.start_turn(task)
        
        # Check safety
        safety_ok, safety_msg = self._pre_execution_safety(task)
        if not safety_ok:
            return {
                "success": False,
                "error": safety_msg,
                "stage": "safety_check"
            }
        
        # Execute with guard
        success, result, error = self.guard.execute_with_guard(
            component="harness",
            func=self._execute_task,
            task=task,
            **kwargs
        )
        
        # End turn
        self.context.end_turn()
        
        elapsed = time.time() - start_time
        
        return {
            "success": success,
            "result": result,
            "error": str(error) if error else None,
            "elapsed_seconds": elapsed,
            "context_stats": self.context.get_statistics()
        }
    
    def _pre_execution_safety(self, task: str) -> tuple[bool, Optional[str]]:
        """Run safety checks before execution."""
        # Check for dangerous commands in task
        safe, msg = SafetyChecker.check_command(task)
        if not safe:
            return False, msg
        return True, None
    
    def _execute_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """Internal task execution (wrapped by guard)."""
        # This is where actual LLM interaction would happen
        # For now, return a placeholder
        return {
            "message": "Harness ready",
            "task_received": task,
            "config_version": self.config.get("harness_version"),
            "available_tools": len(self.tools.list_all()),
            "context_turns": self.context.turn_counter
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete harness status."""
        return {
            "active": self.is_active,
            "uptime_seconds": time.time() - self.initialized_at,
            "config": {
                "version": self.config.get("harness_version"),
                "max_tokens": self.config.get("context.max_tokens"),
                "safety_mode": self.config.get("tools.safety_mode")
            },
            "context": self.context.get_statistics(),
            "guard": self.guard.get_guard_status(),
            "scaffold": self.scaffold.get_statistics(),
            "tools_count": len(self.tools.list_all())
        }
    
    def shutdown(self) -> None:
        """Graceful shutdown."""
        self.scaffold.save()
        self.is_active = False


def main():
    """Main entry point for harness."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            harness = Harness()
            print(json.dumps(harness.get_status(), indent=2))
            
        elif command == "init":
            print("Initializing Harness...")
            harness = Harness()
            print(f"Harness v{harness.config.get('harness_version')} initialized")
            print(f"Tools registered: {len(harness.tools.list_all())}")
            print(f"Context manager: {harness.context.turn_counter} turns")
            
        elif command == "scaffold":
            harness = Harness()
            print(harness.scaffold.create_handoff_brief())
            
        elif command == "guard":
            guard = get_guard()
            print(json.dumps(guard.get_guard_status(), indent=2))
            
        elif command == "tools":
            registry = get_registry()
            register_builtin_tools()
            print(f"Available tools ({len(registry.list_all())}):")
            for name, tool in registry.list_all().items():
                print(f"  {name}: {tool.description} [{tool.danger_level}]")
                
        elif command == "test":
            harness = Harness()
            result = harness.run("Test task from harness")
            print(json.dumps(result, indent=2, default=str))
            
        else:
            print(f"Unknown command: {command}")
            print("Available: status, init, scaffold, guard, tools, test")
    else:
        # Interactive mode - show status
        harness = Harness()
        status = harness.get_status()
        print("Harness Engineering System")
        print("=" * 40)
        print(f"Version: {status['config']['version']}")
        print(f"Uptime: {status['uptime_seconds']:.1f}s")
        print(f"Active: {status['active']}")
        print(f"Context Turns: {status['context']['total_turns']}")
        print(f"Tools: {status['tools_count']}")
        print(f"Safety Mode: {status['config']['safety_mode']}")


if __name__ == "__main__":
    main()
