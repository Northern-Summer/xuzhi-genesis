#!/usr/bin/env python3
"""
Harness Engineering - Guards (Error Handling & Safety)
=======================================================
Circuit breakers, rate limiting, error recovery, and safety guards.
Based on research: Netflix Hystrix, TensorFlow's safety patterns.
"""

import time
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import sys

class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = 1      # Minor issue, can retry immediately
    MEDIUM = 2   # Significant issue, backoff recommended
    HIGH = 3     # Serious issue, circuit break needed
    CRITICAL = 4 # System-level issue, full stop

@dataclass
class GuardError:
    """Represents an error caught by guards."""
    message: str
    severity: ErrorSeverity
    source: str  # tool name, system component, etc.
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    
    def __str__(self) -> str:
        return f"[{self.severity.name}] {self.source}: {self.message}"

@dataclass 
class CircuitState:
    """State for circuit breaker."""
    state: str = "closed"  # closed, open, half_open
    failure_count: int = 0
    last_failure_time: float = 0
    last_failure_type: Optional[str] = None
    
    def record_failure(self, error_type: str) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.last_failure_type = error_type
    
    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "closed"
    
    def should_allow_request(self, timeout: float) -> bool:
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > timeout:
                self.state = "half_open"
                return True
            return False
        else:  # half_open
            return True

class GuardRail:
    """
    Safety guard that intercepts errors and enforces limits.
    
    Features:
    - Circuit breaker pattern
    - Rate limiting with backoff
    - Error threshold detection
    - Recovery suggestions
    """
    
    def __init__(
        self,
        error_threshold: int = 3,
        timeout_seconds: float = 60,
        retry_backoff: float = 1.5,
        max_retries: int = 2
    ):
        self.error_threshold = error_threshold
        self.timeout_seconds = timeout_seconds
        self.retry_backoff = retry_backoff
        self.max_retries = max_retries
        
        self._circuits: Dict[str, CircuitState] = defaultdict(CircuitState)
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._error_history: List[GuardError] = []
        self._lock = threading.Lock()
        
    def check_circuit(self, component: str) -> bool:
        """Check if circuit allows requests."""
        circuit = self._circuits[component]
        return circuit.should_allow_request(self.timeout_seconds)
    
    def record_error(self, error: GuardError) -> None:
        """Record an error and update circuit state."""
        with self._lock:
            self._error_history.append(error)
            
            # Update circuit
            circuit = self._circuits[error.source]
            if error.severity.value >= ErrorSeverity.HIGH.value:
                circuit.record_failure(error.source)
                
                if circuit.failure_count >= self.error_threshold:
                    circuit.state = "open"
                    print(f"[GUARD] Circuit OPEN for {error.source} after {circuit.failure_count} failures",
                          file=sys.stderr)
            
            # Trim error history
            if len(self._error_history) > 100:
                self._error_history = self._error_history[-50:]
    
    def record_success(self, component: str) -> None:
        """Record successful operation."""
        with self._lock:
            circuit = self._circuits[component]
            circuit.record_success()
    
    def check_rate_limit(self, key: str, max_requests: int, window_seconds: float) -> bool:
        """Check if rate limit is exceeded."""
        now = time.time()
        window_start = now - window_seconds
        
        with self._lock:
            # Clean old entries
            self._rate_limits[key] = [
                t for t in self._rate_limits[key] if t > window_start
            ]
            
            if len(self._rate_limits[key]) >= max_requests:
                return False
            
            self._rate_limits[key].append(now)
            return True
    
    def get_backoff_delay(self, attempt: int, base_delay: float = 1.0) -> float:
        """Calculate exponential backoff delay."""
        return base_delay * (self.retry_backoff ** attempt)
    
    def execute_with_guard(
        self,
        component: str,
        func: Callable,
        *args,
        **kwargs
    ) -> tuple[bool, Any, Optional[GuardError]]:
        """
        Execute function with circuit breaker protection.
        Returns (success, result, error).
        """
        # Check circuit
        if not self.check_circuit(component):
            error = GuardError(
                message=f"Circuit open for {component}",
                severity=ErrorSeverity.HIGH,
                source=component,
                retryable=True
            )
            return False, None, error
        
        # Check rate limit
        if not self.check_rate_limit(component, max_requests=30, window_seconds=60):
            error = GuardError(
                message=f"Rate limit exceeded for {component}",
                severity=ErrorSeverity.MEDIUM,
                source=component,
                retryable=True
            )
            return False, None, error
        
        # Execute with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self.record_success(component)
                return True, result, None
            except Exception as e:
                last_error = GuardError(
                    message=str(e),
                    severity=self._classify_exception(e),
                    source=component,
                    retryable=attempt < self.max_retries
                )
                self.record_error(last_error)
                
                if attempt < self.max_retries:
                    delay = self.get_backoff_delay(attempt)
                    time.sleep(delay)
        
        return False, None, last_error
    
    def _classify_exception(self, e: Exception) -> ErrorSeverity:
        """Classify exception severity."""
        error_msg = str(e).lower()
        
        if "timeout" in error_msg or "timed out" in error_msg:
            return ErrorSeverity.MEDIUM
        elif "rate limit" in error_msg or "429" in error_msg:
            return ErrorSeverity.MEDIUM
        elif "unauthorized" in error_msg or "auth" in error_msg:
            return ErrorSeverity.HIGH
        elif "not found" in error_msg or "404" in error_msg:
            return ErrorSeverity.LOW
        elif "connection" in error_msg or "network" in error_msg:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.MEDIUM
    
    def get_guard_status(self) -> Dict[str, Any]:
        """Get current guard status for monitoring."""
        return {
            "circuits": {
                name: {
                    "state": circuit.state,
                    "failures": circuit.failure_count,
                    "last_failure": circuit.last_failure_time
                }
                for name, circuit in self._circuits.items()
            },
            "error_history_count": len(self._error_history),
            "recent_errors": [
                str(e) for e in self._error_history[-5:]
            ],
            "rate_limits": {
                key: len(times) 
                for key, times in self._rate_limits.items()
            }
        }
    
    def reset(self) -> None:
        """Reset all guards to initial state."""
        with self._lock:
            self._circuits.clear()
            self._rate_limits.clear()
            self._error_history.clear()


# Global guard instance
_guard_instance: Optional[GuardRail] = None

def get_guard() -> GuardRail:
    """Get singleton guard instance."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = GuardRail()
    return _guard_instance


class SafetyChecker:
    """
    Pre-execution safety checks for tools and operations.
    """
    
    # Patterns that indicate potentially dangerous operations
    DANGEROUS_PATTERNS = [
        ("rm -rf", "Recursive force removal"),
        ("sudo su", "Privilege escalation attempt"),
        (":(){:|:&};:", "Fork bomb pattern"),
        ("chmod 777", "World-writable permission"),
        ("eval", "Dynamic code execution"),
        ("exec ", "Shell execution"),
    ]
    
    # Files/paths that should never be modified without explicit confirmation
    PROTECTED_PATTERNS = [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "~/.ssh/",
        "/sys/",
        "/proc/",
        "/dev/",
    ]
    
    @classmethod
    def check_command(cls, command: str) -> tuple[bool, Optional[str]]:
        """Check if command is safe to execute."""
        cmd_lower = command.lower()
        
        for pattern, description in cls.DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_lower:
                return False, f"Dangerous pattern detected: {description}"
        
        return True, None
    
    @classmethod
    def check_path(cls, path: str) -> tuple[bool, Optional[str]]:
        """Check if path operation is safe."""
        path_expanded = str(Path(path).expanduser().resolve())
        
        for protected in cls.PROTECTED_PATTERNS:
            protected_expanded = str(Path(protected).expanduser().resolve())
            if path_expanded.startswith(protected_expanded):
                return False, f"Protected path: {protected}"
        
        return True, None


if __name__ == "__main__":
    guard = get_guard()
    
    # Test circuit breaker
    print("Guard Status Test")
    print(f"  Circuits: {len(guard._circuits)}")
    
    # Test safety checker
    safe, msg = SafetyChecker.check_command("ls -la")
    print(f"  'ls -la' safe: {safe}")
    
    safe, msg = SafetyChecker.check_command("rm -rf /")
    print(f"  'rm -rf /' safe: {safe}, reason: {msg}")
