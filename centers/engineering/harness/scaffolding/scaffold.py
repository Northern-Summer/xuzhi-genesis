#!/usr/bin/env python3
"""
Harness Engineering - Scaffolding (Handoff System)
===================================================
Enables seamless handoff between agent sessions.
Based on research: OpenAI's context extension, Anthropic's multi-turn memory.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import sys

@dataclass
class HandoffState:
    """Complete state for handoff to future self."""
    session_id: str
    created_at: float
    updated_at: float
    task_stack: List[Dict] = field(default_factory=list)
    current_task: Optional[Dict] = None
    completed_tasks: List[Dict] = field(default_factory=list)
    blocked_tasks: List[Dict] = field(default_factory=list)
    context_summary: str = ""
    pending_decisions: List[Dict] = field(default_factory=list)
    discovered_facts: List[str] = field(default_factory=list)
    failed_attempts: List[Dict] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)  # checkpoint file paths
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "task_stack": self.task_stack,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "blocked_tasks": self.blocked_tasks,
            "context_summary": self.context_summary,
            "pending_decisions": self.pending_decisions,
            "discovered_facts": self.discovered_facts,
            "failed_attempts": self.failed_attempts,
            "checkpoints": self.checkpoints
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'HandoffState':
        return cls(
            session_id=d.get("session_id", ""),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
            task_stack=d.get("task_stack", []),
            current_task=d.get("current_task"),
            completed_tasks=d.get("completed_tasks", []),
            blocked_tasks=d.get("blocked_tasks", []),
            context_summary=d.get("context_summary", ""),
            pending_decisions=d.get("pending_decisions", []),
            discovered_facts=d.get("discovered_facts", []),
            failed_attempts=d.get("failed_attempts", []),
            checkpoints=d.get("checkpoints", [])
        )

class Scaffold:
    """
    Scaffolding system for agent work handoff.
    
    Key concepts:
    - Task Stack: What needs to be done (LIFO)
    - Current Task: What's being worked on now
    - Completed Tasks: History of finished work
    - Blocked Tasks: Tasks waiting on dependencies
    - Context Summary: Narrative of what's happening
    - Pending Decisions: Choices that need human/agent input
    - Discovered Facts: Key learnings to preserve
    - Failed Attempts: What didn't work (and why)
    """
    
    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.home() / "xuzhi_genesis" / "centers" / "engineering" / "harness"
        self.scaffolding_dir = self.workspace / "scaffolding"
        self.scaffolding_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = self._generate_session_id()
        self.state = self._load_state()
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID based on time and random."""
        timestamp = str(time.time()).encode()
        random_bytes = str(time.process_time()).encode()
        return hashlib.md5(timestamp + random_bytes).hexdigest()[:12]
    
    def _state_file(self) -> Path:
        """Get path to current state file."""
        return self.scaffolding_dir / f"state_{self.session_id}.json"
    
    def _load_state(self) -> HandoffState:
        """Load existing state or create new."""
        # Try to find most recent state
        states = sorted(self.scaffolding_dir.glob("state_*.json"), 
                       key=lambda p: p.stat().st_mtime, 
                       reverse=True)
        
        if states:
            try:
                with open(states[0]) as f:
                    data = json.load(f)
                return HandoffState.from_dict(data)
            except Exception:
                pass
        
        return HandoffState(
            session_id=self.session_id,
            created_at=time.time(),
            updated_at=time.time()
        )
    
    def save(self) -> None:
        """Save current state to disk."""
        self.state.updated_at = time.time()
        state_file = self._state_file()
        
        with open(state_file, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)
        
        # Update checkpoint list
        if str(state_file) not in self.state.checkpoints:
            self.state.checkpoints.append(str(state_file))
        
        # Keep only last 10 state files
        self._prune_old_states()
    
    def _prune_old_states(self) -> None:
        """Keep only last 10 state files."""
        states = sorted(self.scaffolding_dir.glob("state_*.json"),
                       key=lambda p: p.stat().st_mtime,
                       reverse=True)
        for old_state in states[10:]:
            try:
                old_state.unlink()
            except Exception:
                pass
    
    # ===== Task Management =====
    
    def push_task(self, title: str, description: str, priority: str = "medium", metadata: Optional[Dict] = None) -> None:
        """Add a task to the stack."""
        task = {
            "title": title,
            "description": description,
            "priority": priority,  # low, medium, high, critical
            "status": "pending",
            "created_at": time.time(),
            "metadata": metadata or {}
        }
        self.state.task_stack.append(task)
        self.state.current_task = task
        self.save()
    
    def complete_current_task(self, result: Optional[str] = None) -> Optional[Dict]:
        """Mark current task as completed."""
        if not self.state.current_task:
            return None
        
        completed = self.state.current_task.copy()
        completed["status"] = "completed"
        completed["completed_at"] = time.time()
        completed["result"] = result or "No explicit result"
        
        self.state.completed_tasks.append(completed)
        self.state.task_stack = [t for t in self.state.task_stack if t != completed]
        self.state.current_task = self.state.task_stack[-1] if self.state.task_stack else None
        self.save()
        
        return completed
    
    def block_task(self, reason: str, dependency: Optional[str] = None) -> None:
        """Move current task to blocked."""
        if not self.state.current_task:
            return
        
        blocked = self.state.current_task.copy()
        blocked["status"] = "blocked"
        blocked["blocked_reason"] = reason
        blocked["dependency"] = dependency
        blocked["blocked_at"] = time.time()
        
        self.state.blocked_tasks.append(blocked)
        self.state.task_stack = [t for t in self.state.task_stack if t != blocked]
        self.state.current_task = self.state.task_stack[-1] if self.state.task_stack else None
        self.save()
    
    def record_failed_attempt(self, approach: str, error: str, lesson: str) -> None:
        """Record a failed approach and what was learned."""
        self.state.failed_attempts.append({
            "approach": approach,
            "error": error,
            "lesson": lesson,
            "timestamp": time.time()
        })
        self.save()
    
    # ===== Context & Knowledge =====
    
    def update_context_summary(self, summary: str) -> None:
        """Update the narrative summary."""
        self.state.context_summary = summary
        self.save()
    
    def add_fact(self, fact: str) -> None:
        """Add a discovered fact."""
        if fact not in self.state.discovered_facts:
            self.state.discovered_facts.append(fact)
            self.save()
    
    def add_pending_decision(self, question: str, options: List[str], context: str) -> None:
        """Add a decision that needs to be made."""
        self.state.pending_decisions.append({
            "question": question,
            "options": options,
            "context": context,
            "asked_at": time.time()
        })
        self.save()
    
    def resolve_decision(self, question: str, choice: str, reasoning: str) -> None:
        """Resolve a pending decision."""
        for decision in self.state.pending_decisions:
            if decision["question"] == question:
                decision["resolved"] = True
                decision["choice"] = choice
                decision["reasoning"] = reasoning
                decision["resolved_at"] = time.time()
                self.save()
                return
    
    # ===== Handoff =====
    
    def create_handoff_brief(self) -> str:
        """
        Create a human-readable handoff brief for future self.
        This is the key artifact that enables continuity.
        """
        lines = [
            "=" * 60,
            "HARNESS HANDOFF BRIEF",
            "=" * 60,
            f"Session ID: {self.session_id}",
            f"Created: {datetime.fromtimestamp(self.state.created_at).isoformat()}",
            f"Updated: {datetime.fromtimestamp(self.state.updated_at).isoformat()}",
            "",
            "# CURRENT STATUS",
            "-" * 40,
        ]
        
        if self.state.current_task:
            lines.append(f"Working on: {self.state.current_task['title']}")
            lines.append(f"Description: {self.state.current_task.get('description', 'N/A')}")
            lines.append(f"Priority: {self.state.current_task.get('priority', 'medium')}")
        else:
            lines.append("No active task")
        
        lines.extend(["", "# TASK STACK", "-" * 40])
        if self.state.task_stack:
            for i, task in enumerate(reversed(self.state.task_stack[-5:]), 1):
                lines.append(f"{i}. [{task['priority']}] {task['title']}")
        else:
            lines.append("(empty)")
        
        lines.extend(["", "# COMPLETED TASKS", "-" * 40])
        if self.state.completed_tasks:
            for task in self.state.completed_tasks[-5:]:
                lines.append(f"✓ {task['title']}")
                if task.get('result'):
                    lines.append(f"  → {task['result'][:100]}")
        else:
            lines.append("(none)")
        
        lines.extend(["", "# BLOCKED TASKS", "-" * 40])
        if self.state.blocked_tasks:
            for task in self.state.blocked_tasks:
                lines.append(f"⊗ {task['title']}")
                lines.append(f"  Reason: {task.get('blocked_reason', 'unknown')}")
        
        lines.extend(["", "# FAILED ATTEMPTS (LESSONS)", "-" * 40])
        if self.state.failed_attempts:
            for attempt in self.state.failed_attempts[-3:]:
                lines.append(f"✗ {attempt['approach']}")
                lines.append(f"  Error: {attempt['error'][:80]}")
                lines.append(f"  Lesson: {attempt['lesson']}")
        
        lines.extend(["", "# DISCOVERED FACTS", "-" * 40])
        if self.state.discovered_facts:
            for fact in self.state.discovered_facts[-10:]:
                lines.append(f"• {fact}")
        else:
            lines.append("(none)")
        
        lines.extend(["", "# PENDING DECISIONS", "-" * 40])
        if self.state.pending_decisions:
            unresolved = [d for d in self.state.pending_decisions if not d.get("resolved")]
            for decision in unresolved:
                lines.append(f"? {decision['question']}")
                for opt in decision.get('options', []):
                    lines.append(f"  - {opt}")
        else:
            lines.append("(none)")
        
        lines.extend(["", "# CONTEXT SUMMARY", "-" * 40])
        lines.append(self.state.context_summary or "(not set)")
        
        lines.extend(["", "=" * 60])
        
        return "\n".join(lines)
    
    def get_next_action_suggestion(self) -> Optional[str]:
        """Suggest what to do next based on state."""
        if self.state.current_task:
            return f"Continue with: {self.state.current_task['title']}"
        
        if self.state.task_stack:
            next_task = self.state.task_stack[-1]
            return f"Next task: {next_task['title']} [{next_task['priority']}]"
        
        if self.state.pending_decisions:
            unresolved = [d for d in self.state.pending_decisions if not d.get("resolved")]
            if unresolved:
                return f"Pending decision: {unresolved[0]['question']}"
        
        return None
    
    def get_statistics(self) -> Dict:
        """Get scaffolding statistics."""
        return {
            "session_id": self.session_id,
            "session_age_seconds": time.time() - self.state.created_at,
            "total_tasks": len(self.state.task_stack) + len(self.state.completed_tasks),
            "completed_tasks": len(self.state.completed_tasks),
            "blocked_tasks": len(self.state.blocked_tasks),
            "failed_attempts": len(self.state.failed_attempts),
            "discovered_facts": len(self.state.discovered_facts),
            "pending_decisions": len([d for d in self.state.pending_decisions if not d.get("resolved")]),
            "checkpoints": len(self.state.checkpoints)
        }


if __name__ == "__main__":
    scaffold = Scaffold()
    
    # Test task management
    scaffold.push_task(
        "Design harness core",
        "Create the core configuration and context management modules",
        priority="high"
    )
    
    scaffold.push_task(
        "Implement guards",
        "Build error handling and safety guard system",
        priority="high"
    )
    
    scaffold.complete_current_task("Core modules created successfully")
    
    scaffold.add_fact("Python 3.8+ required for dataclass field defaults")
    scaffold.add_fact("Threading needed for concurrent guard operations")
    
    scaffold.update_context_summary(
        "Building the Harness engineering system for OpenClaw. "
        "Focus is on creating a robust framework for LLM interaction "
        "with proper error handling, context management, and session handoff."
    )
    
    # Generate handoff brief
    brief = scaffold.create_handoff_brief()
    print(brief)
    
    print("\n" + "=" * 40)
    print("STATISTICS")
    print("=" * 40)
    stats = scaffold.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nNext action: {scaffold.get_next_action_suggestion()}")
