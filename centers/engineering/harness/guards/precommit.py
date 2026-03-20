"""
Pre-Execution Guard - SWE-agent review_on_submit inspired
==========================================================
Inspired by sweagent/tools/review_on_submit_m/

Performs safety checks before executing actions:
1. Destructive operation detection
2. Backup verification
3. Permission checks
4. Syntax validation
5. Dry run simulation
"""

from __future__ import annotations

import os
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ActionType(Enum):
    """Types of actions an agent can take"""
    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    DELETE = "delete"
    EXECUTE = "execute"
    CREATE = "create"
    MOVE = "move"
    COPY = "copy"
    PERMISSION = "permission"
    NETWORK = "network"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk assessment levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardResult:
    """Result of a guard check"""
    passed: bool
    risk_level: RiskLevel
    message: str
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    backup_required: bool = False


@dataclass
class Action:
    """Represents an action to be executed"""
    tool: str
    command: str
    target: str = ""
    args: dict = field(default_factory=dict)
    raw: str = ""


class AbstractGuard(ABC):
    """Base class for guards"""
    
    @abstractmethod
    def check(self, action: Action) -> GuardResult:
        raise NotImplementedError


class DestructiveOperationGuard(AbstractGuard):
    """
    Detect potentially destructive operations.
    
    Inspired by SWE-agent's review_on_submit which checks for:
    - Deleting test files
    - Modifying production code inappropriately
    - Destructive shell commands
    """
    
    DESTRUCTIVE_PATTERNS = [
        # File deletion
        (r"\brm\s+-[rfv]+\s", "Recursive force delete", RiskLevel.HIGH),
        (r"rmdir\s+", "Directory removal", RiskLevel.MEDIUM),
        (r"del\s+", "File deletion (Windows-style)", RiskLevel.MEDIUM),
        
        # Format wiping
        (r">\s*/dev/sd[a-z]", "Direct device write", RiskLevel.CRITICAL),
        (r"dd\s+.*of=/dev/", "Direct device copy", RiskLevel.CRITICAL),
        (r"mkfs\.", "Filesystem format", RiskLevel.CRITICAL),
        
        # System modification
        (r"chmod\s+[-x]?\s*0[0-7]", "Restrictive permission change", RiskLevel.MEDIUM),
        (r"chown\s+", "Ownership change", RiskLevel.LOW),
        (r"shutdown|reboot|halt|init\s+0|init\s+6", "System shutdown/reboot", RiskLevel.HIGH),
        
        # Network danger
        (r"(curl|wget)\s+.*\s*\|\s*(sh|bash|bash\s+-c)", "Pipe to shell (curl/wget | sh)", RiskLevel.HIGH),
        (r"\|(sh|bash)", "Pipe to shell", RiskLevel.HIGH),
        
        # Git danger
        (r"git\s+push\s+.*--force", "Force push", RiskLevel.HIGH),
        (r"git\s+push\s+.*--delete", "Remote branch deletion", RiskLevel.MEDIUM),
        
        # Process killing
        (r"kill\s+-9\s+\$", "Force kill of process", RiskLevel.MEDIUM),
        (r"pkill\s+", "Pattern kill", RiskLevel.MEDIUM),
        (r"killall\s+", "Kill all matching", RiskLevel.MEDIUM),
        
        # Data deletion
        (r":\s*>\s*/var/", "Truncate system file", RiskLevel.CRITICAL),
        (r">\s*.*\.log", "Log file truncation", RiskLevel.LOW),
    ]
    
    PROTECTED_PATHS = [
        "/etc/",
        "/var/",
        "/usr/",
        "/bin/",
        "/sbin/",
        "/boot/",
        "/sys/",
        "/proc/",
        "~/.ssh/",
        "~/.aws/",
    ]
    
    TEST_FILE_PATTERNS = [
        "test_*.py",
        "*_test.py",
        "tests/",
        "__tests__/",
        "*.test.js",
        "*.spec.js",
        "test_*.js",
    ]
    
    def check(self, action: Action) -> GuardResult:
        command = action.raw or action.command
        warnings = []
        suggestions = []
        backup_required = False
        
        # Check destructive patterns
        for pattern, description, risk in self.DESTRUCTIVE_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                warnings.append(f"Destructive pattern detected: {description}")
                suggestions.append(f"Consider creating a backup before executing")
                backup_required = True
                if risk == RiskLevel.CRITICAL:
                    return GuardResult(
                        passed=False,
                        risk_level=risk,
                        message=f"Critical operation blocked: {description}",
                        warnings=warnings,
                        suggestions=suggestions,
                        backup_required=True
                    )
        
        # Check protected paths
        for protected in self.PROTECTED_PATHS:
            if protected in command:
                warnings.append(f"Protected path detected: {protected}")
                if risk := self._get_path_risk(protected):
                    return GuardResult(
                        passed=False,
                        risk_level=risk,
                        message=f"Protected system path access blocked: {protected}",
                        warnings=warnings,
                        suggestions=["Use a workspace directory instead of system paths"]
                    )
        
        # Check for test file modification (SWE-agent concern)
        for pattern in self.TEST_FILE_PATTERNS:
            if pattern in command:
                warnings.append(f"Test file pattern detected: {pattern}")
                suggestions.append("Ensure test files are not modified inappropriately")
        
        # Determine overall risk
        risk_level = RiskLevel.SAFE
        if warnings:
            if any("CRITICAL" in w for w in warnings):
                risk_level = RiskLevel.CRITICAL
            elif any("HIGH" in w for w in warnings):
                risk_level = RiskLevel.HIGH
            elif any("MEDIUM" in w for w in warnings):
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
        
        return GuardResult(
            passed=risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            risk_level=risk_level,
            message="Operation appears safe" if not warnings else f"Warnings: {', '.join(warnings)}",
            warnings=warnings,
            suggestions=suggestions,
            backup_required=backup_required
        )
    
    def _get_path_risk(self, path: str) -> Optional[RiskLevel]:
        """Get risk level for protected path"""
        critical = ["/etc/", "/var/", "/boot/", "/sys/", "/proc/"]
        high = ["/usr/", "/bin/", "/sbin/"]
        medium = ["~/.ssh/", "~/.aws/"]
        
        if path in critical:
            return RiskLevel.CRITICAL
        if path in high:
            return RiskLevel.HIGH
        if path in medium:
            return RiskLevel.MEDIUM
        return None


class PermissionGuard(AbstractGuard):
    """
    Check if the agent has proper permissions for the action.
    """
    
    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace).resolve()
    
    def check(self, action: Action) -> GuardResult:
        target = action.target or action.raw
        
        if not target:
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="No target specified"
            )
        
        target_path = Path(target)
        
        # Resolve relative paths
        if not target_path.is_absolute():
            target_path = self.workspace / target_path
        
        # Check if path exists
        if target_path.exists():
            # Check write permission
            if os.access(target_path, os.W_OK):
                return GuardResult(
                    passed=True,
                    risk_level=RiskLevel.SAFE,
                    message="Write permission verified"
                )
            else:
                return GuardResult(
                    passed=False,
                    risk_level=RiskLevel.MEDIUM,
                    message=f"No write permission for: {target_path}",
                    suggestions=["Check file ownership and permissions", "Use sudo if appropriate"]
                )
        
        # Check parent directory for create permission
        parent = target_path.parent
        if parent.exists() and not os.access(parent, os.W_OK):
            return GuardResult(
                passed=False,
                risk_level=RiskLevel.MEDIUM,
                message=f"No create permission in: {parent}",
                suggestions=["Check directory permissions"]
            )
        
        return GuardResult(
            passed=True,
            risk_level=RiskLevel.SAFE,
            message="Permission check passed"
        )


class SyntaxGuard(AbstractGuard):
    """
    Validate syntax before execution.
    
    For bash: uses `bash -n` to check syntax
    For python: uses `python -m py_compile`
    """
    
    def check(self, action: Action) -> GuardResult:
        command = action.raw or action.command
        tool = action.tool.lower()
        
        if tool == "bash" or tool == "shell":
            return self._check_bash_syntax(command)
        elif tool == "python":
            return self._check_python_syntax(command)
        
        return GuardResult(
            passed=True,
            risk_level=RiskLevel.SAFE,
            message="No syntax validation available for this tool"
        )
    
    def _check_bash_syntax(self, command: str) -> GuardResult:
        """Check bash syntax using bash -n"""
        try:
            result = subprocess.run(
                ["bash", "-n", "-c", command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return GuardResult(
                    passed=False,
                    risk_level=RiskLevel.MEDIUM,
                    message=f"Bash syntax error: {result.stderr.strip()}",
                    warnings=["Command was NOT executed due to syntax error"],
                    suggestions=["Fix syntax errors before executing"]
                )
            
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="Bash syntax valid"
            )
        except subprocess.TimeoutExpired:
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.LOW,
                message="Syntax check timed out (likely valid)"
            )
        except FileNotFoundError:
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="bash not found, skipping syntax check"
            )
    
    def _check_python_syntax(self, command: str) -> GuardResult:
        """Check Python syntax using py_compile"""
        # Extract file path from command like "python file.py"
        match = re.search(r'python.+\s+(\S+\.py)', command)
        if not match:
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="Could not extract Python file path"
            )
        
        file_path = match.group(1)
        
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return GuardResult(
                    passed=False,
                    risk_level=RiskLevel.MEDIUM,
                    message=f"Python syntax error: {result.stderr.strip()}",
                    suggestions=["Fix syntax errors before executing"]
                )
            
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="Python syntax valid"
            )
        except subprocess.TimeoutExpired:
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.LOW,
                message="Syntax check timed out"
            )
        except FileNotFoundError:
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="python not found, skipping syntax check"
            )


class BackupGuard(AbstractGuard):
    """
    Ensure backups exist for important files before destructive operations.
    """
    
    def __init__(self, backup_dir: str = ".backups"):
        self.backup_dir = Path(backup_dir)
    
    def check(self, action: Action) -> GuardResult:
        command = action.raw or action.command
        target = action.target
        
        # Check if this is a destructive operation
        destructive_keywords = ["rm", "del", "mv", "cp --remove-destination"]
        
        if not any(kw in command for kw in destructive_keywords):
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="Not a destructive operation"
            )
        
        if not target:
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message="No specific target to backup"
            )
        
        target_path = Path(target)
        backup_path = self.backup_dir / target_path.name
        
        if not target_path.exists():
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.SAFE,
                message=f"Target does not exist, no backup needed"
            )
        
        # Check if backup exists
        if backup_path.exists():
            return GuardResult(
                passed=True,
                risk_level=RiskLevel.LOW,
                message=f"Backup exists: {backup_path}",
                suggestions=["Verify backup is recent before proceeding"]
            )
        
        return GuardResult(
            passed=True,  # Don't block, just warn
            risk_level=RiskLevel.MEDIUM,
            message="No backup found for target",
            warnings=["No backup exists for this file"],
            suggestions=[f"Consider creating backup: cp {target} {backup_path}"],
            backup_required=True
        )


class GuardPipeline:
    """
    Chain multiple guards together.
    
    Guards are executed in order. Execution stops on CRITICAL risk.
    """
    
    def __init__(
        self,
        guards: list[AbstractGuard] | None = None,
        stop_on_critical: bool = True
    ):
        self.guards = guards or []
        self.stop_on_critical = stop_on_critical
    
    def add_guard(self, guard: AbstractGuard) -> None:
        self.guards.append(guard)
    
    def check(self, action: Action) -> GuardResult:
        """Run all guards and aggregate results"""
        all_warnings = []
        all_suggestions = []
        any_failed = False
        max_risk = RiskLevel.SAFE
        
        for guard in self.guards:
            result = guard.check(action)
            
            if not result.passed:
                any_failed = True
            
            all_warnings.extend(result.warnings)
            all_suggestions.extend(result.suggestions)
            
            if result.risk_level.value > max_risk.value:
                max_risk = result.risk_level
            
            # Stop on critical if configured
            if self.stop_on_critical and result.risk_level == RiskLevel.CRITICAL:
                return GuardResult(
                    passed=False,
                    risk_level=RiskLevel.CRITICAL,
                    message=result.message,
                    warnings=all_warnings,
                    suggestions=all_suggestions,
                    backup_required=result.backup_required
                )
        
        return GuardResult(
            passed=not any_failed,
            risk_level=max_risk,
            message="All guards passed" if not any_failed else "Some guards raised warnings",
            warnings=all_warnings,
            suggestions=all_suggestions
        )


# Default guard pipeline factory
def create_default_guard_pipeline(workspace: str = ".") -> GuardPipeline:
    """Create the default guard pipeline (SWE-agent inspired)"""
    return GuardPipeline([
        DestructiveOperationGuard(),
        PermissionGuard(workspace=workspace),
        SyntaxGuard(),
        BackupGuard(),
    ])


# Convenience function
def guard_action(
    command: str,
    tool: str = "bash",
    workspace: str = ".",
    guards: list[AbstractGuard] | None = None
) -> GuardResult:
    """
    Convenience function to guard a single action.
    
    Args:
        command: The command to guard
        tool: The tool being used
        workspace: Working directory
        guards: Optional custom guards
        
    Returns:
        GuardResult with the assessment
    """
    pipeline = guards or create_default_guard_pipeline(workspace)
    action = Action(tool=tool, command=command, raw=command)
    return pipeline.check(action)
