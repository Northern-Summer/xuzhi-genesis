#!/usr/bin/env python3
"""
Harness Engineering - Tools Registry
=====================================
Central registry of available tools with safety wrappers.
"""

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

class ToolMetadata:
    """Metadata for a registered tool."""
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        func: Callable,
        danger_level: str = "safe",  # safe, caution, dangerous
        requires_confirmation: bool = False,
        examples: Optional[List[str]] = None,
        parameters: Optional[Dict] = None
    ):
        self.name = name
        self.description = description
        self.category = category
        self.func = func
        self.danger_level = danger_level
        self.requires_confirmation = requires_confirmation
        self.examples = examples or []
        self.parameters = parameters or {}
        
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "danger_level": self.danger_level,
            "requires_confirmation": self.requires_confirmation,
            "examples": self.examples,
            "parameters": self.parameters
        }

class ToolsRegistry:
    """
    Central registry for all available tools.
    
    Tools are categorized and wrapped with safety checks.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._categories: Dict[str, List[str]] = {}
        self._load_builtin_tools()
    
    def _load_builtin_tools(self) -> None:
        """Load built-in tools from the tools directory."""
        tools_dir = Path(__file__).parent
        if not tools_dir.exists():
            return
            
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name.startswith("_"):
                continue
            try:
                module_name = tool_file.stem
                spec = importlib.util.spec_from_file_location(module_name, tool_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Look for tool classes or functions
                    for name, obj in inspect.getmembers(module):
                        if name.startswith("_"):
                            continue
                        if isinstance(obj, type) and hasattr(obj, "execute"):
                            self.register(obj())
                        elif callable(obj) and not name.startswith("_"):
                            pass  # Handle functions differently
            except Exception as e:
                print(f"[TOOLS] Failed to load {tool_file}: {e}", file=sys.stderr)
    
    def register(
        self,
        tool: ToolMetadata,
        override: bool = False
    ) -> bool:
        """Register a tool."""
        if tool.name in self._tools and not override:
            return False
        
        self._tools[tool.name] = tool
        
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)
        
        return True
    
    def get(self, name: str) -> Optional[ToolMetadata]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_by_category(self, category: str) -> List[ToolMetadata]:
        """List all tools in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def list_all(self) -> Dict[str, ToolMetadata]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self._categories.keys())
    
    def search(self, query: str) -> List[ToolMetadata]:
        """Search tools by name or description."""
        query_lower = query.lower()
        results = []
        for tool in self._tools.values():
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                results.append(tool)
        return results
    
    def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        safety_check: bool = True
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute a tool with safety checks.
        Returns (success, result, error_message).
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return False, None, f"Tool not found: {tool_name}"
        
        # Safety check
        if safety_check and tool.danger_level == "dangerous":
            return False, None, f"Tool {tool_name} requires confirmation before execution"
        
        try:
            # Execute tool
            result = tool.func(**parameters)
            return True, result, None
        except TypeError as e:
            # Parameter mismatch
            return False, None, f"Parameter error: {e}"
        except Exception as e:
            return False, None, f"Execution error: {e}"
    
    def generate_tool_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for all tools (for LLM function calling)."""
        schema = {
            "tools": []
        }
        
        for tool in self._tools.values():
            tool_schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.parameters.get("properties", {}),
                    "required": tool.parameters.get("required", [])
                }
            }
            schema["tools"].append(tool_schema)
        
        return schema


# Global registry instance
_registry: Optional[ToolsRegistry] = None

def get_registry() -> ToolsRegistry:
    """Get singleton tools registry."""
    global _registry
    if _registry is None:
        _registry = ToolsRegistry()
    return _registry


# Built-in tool examples
class FileReadTool:
    """Tool for safely reading files."""
    
    def __init__(self):
        self.name = "file_read"
        self.description = "Read contents of a text file"
        self.category = "filesystem"
        self.danger_level = "safe"
    
    def execute(self, path: str, offset: int = 0, limit: int = 1000) -> Dict[str, Any]:
        """Read file with optional offset and limit."""
        try:
            file_path = Path(path).expanduser()
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(file_path) as f:
                lines = f.readlines()
            
            start = min(offset, len(lines))
            end = min(offset + limit, len(lines))
            
            return {
                "success": True,
                "content": "".join(lines[start:end]),
                "total_lines": len(lines),
                "offset": start,
                "limit": end - start
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class FileWriteTool:
    """Tool for safely writing files."""
    
    def __init__(self):
        self.name = "file_write"
        self.description = "Write content to a file (creates or overwrites)"
        self.category = "filesystem"
        self.danger_level = "caution"
        self.requires_confirmation = False  # Can auto-confirm for workspace files
    
    def execute(self, path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to file."""
        try:
            file_path = Path(path).expanduser()
            
            # Safety: only allow writes to workspace or harness directories
            workspace = Path.home() / "xuzhi_genesis" / "centers" / "engineering"
            if not str(file_path).startswith(str(workspace)):
                # Also allow openclaw workspace
                oc_workspace = Path.home() / ".openclaw" / "workspace"
                if not str(file_path).startswith(str(oc_workspace)):
                    return {"success": False, "error": "Write outside allowed directories not permitted"}
            
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w") as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(file_path),
                "bytes_written": len(content)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Register built-in tools
def register_builtin_tools():
    """Register built-in tools."""
    registry = get_registry()
    registry.register(FileReadTool())
    registry.register(FileWriteTool())


if __name__ == "__main__":
    registry = get_registry()
    register_builtin_tools()
    
    print(f"Tools Registry")
    print(f"  Categories: {registry.list_categories()}")
    print(f"  Total tools: {len(registry.list_all())}")
    
    # Test file read
    success, result, error = registry.execute("file_read", {"path": "/etc/hostname"})
    print(f"\nFile read test: {success}")
    if success:
        print(f"  Content: {result.get('content', '').strip()}")
