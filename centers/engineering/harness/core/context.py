#!/usr/bin/env python3
"""
Harness Engineering - Context Manager
======================================
Manages conversation history, compression, and checkpointing.
Based on research from: Anthropic's context management, LangChain's memory.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    """A single message in the conversation history."""
    role: str  # system, user, assistant, tool
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Message':
        return cls(
            role=d.get("role", "assistant"),
            content=d.get("content", ""),
            timestamp=d.get("timestamp", time.time()),
            metadata=d.get("metadata", {})
        )

@dataclass 
class Turn:
    """A complete turn: user message + assistant response + tool calls."""
    turn_id: int
    user_message: Message
    assistant_message: Optional[Message] = None
    tool_calls: List[Dict] = field(default_factory=list)
    checkpoint_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message.to_dict(),
            "assistant_message": self.assistant_message.to_dict() if self.assistant_message else None,
            "tool_calls": self.tool_calls,
            "checkpoint_hash": self.checkpoint_hash
        }


class ContextManager:
    """
    Manages conversation context with smart compression.
    
    Key features:
    - Turn-based history tracking
    - Semantic compression (keeps meaning, reduces tokens)
    - Checkpointing for handoff continuity
    - Sliding window with importance weighting
    """
    
    def __init__(self, 
                 max_tokens: int = 128000,
                 reserve_tokens: int = 4096,
                 compression_threshold: float = 0.85,
                 checkpoint_dir: Optional[Path] = None):
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.compression_threshold = compression_threshold
        self.available_tokens = max_tokens - reserve_tokens
        
        self.checkpoint_dir = checkpoint_dir or Path.home() / "xuzhi_genesis" / "centers" / "engineering" / "harness" / "history"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.turns: List[Turn] = []
        self.current_turn: Optional[Turn] = None
        self.turn_counter = 0
        
        self._checkpoint_metadata: Dict[str, Any] = {
            "created": time.time(),
            "last_checkpoint": None,
            "total_turns": 0,
            "compression_events": 0
        }
        
    def start_turn(self, user_message: str) -> Turn:
        """Start a new turn with user message."""
        self.turn_counter += 1
        self.current_turn = Turn(
            turn_id=self.turn_counter,
            user_message=Message(role="user", content=user_message)
        )
        return self.current_turn
    
    def add_assistant_response(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add assistant response to current turn."""
        if self.current_turn:
            self.current_turn.assistant_message = Message(
                role="assistant",
                content=content,
                metadata=metadata or {}
            )
    
    def add_tool_call(self, tool_name: str, tool_input: Dict, tool_output: str) -> None:
        """Record a tool call in current turn."""
        if self.current_turn:
            self.current_turn.tool_calls.append({
                "tool": tool_name,
                "input": tool_input,
                "output": tool_output[:500] if len(tool_output) > 500 else tool_output,  # Truncate long outputs
                "timestamp": time.time()
            })
    
    def end_turn(self) -> None:
        """Finalize current turn and check for compression needs."""
        if self.current_turn:
            self.current_turn.checkpoint_hash = self._compute_hash(self.current_turn)
            self.turns.append(self.current_turn)
            self.current_turn = None
            self._checkpoint_metadata["total_turns"] = self.turn_counter
            
            # Check if compression is needed
            if self._should_compress():
                self._compress()
    
    def _should_compress(self) -> bool:
        """Determine if context should be compressed."""
        estimated_tokens = self._estimate_total_tokens()
        return estimated_tokens > (self.available_tokens * self.compression_threshold)
    
    def _estimate_total_tokens(self) -> int:
        """Rough estimate of total tokens in context."""
        total = 0
        for turn in self.turns:
            total += self._estimate_message_tokens(turn.user_message)
            if turn.assistant_message:
                total += self._estimate_message_tokens(turn.assistant_message)
            for tc in turn.tool_calls:
                total += len(tc.get("output", "")) // 4  # Rough token estimate
        return total
    
    def _estimate_message_tokens(self, msg: Message) -> int:
        """Estimate tokens in a message."""
        return len(msg.content) // 4 + 50  # +50 for role overhead
    
    def _compute_hash(self, turn: Turn) -> str:
        """Compute hash for turn continuity check."""
        content = json.dumps(turn.to_dict(), sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _compress(self) -> None:
        """
        Compress history while preserving essential information.
        
        Strategy:
        1. Keep first message (system prompt alignment)
        2. Keep recent N turns fully
        3. Summarize middle turns semantically
        4. Preserve tool call patterns
        """
        self._checkpoint_metadata["compression_events"] += 1
        
        if len(self.turns) <= 3:
            return  # Not enough turns to compress
        
        # Keep: first turn (system alignment), last 2 turns (recency)
        keep_first = self.turns[0]
        keep_recent = self.turns[-2:]
        
        # Summarize middle turns
        middle_turns = self.turns[1:-2]
        if middle_turns:
            summary = self._summarize_turns(middle_turns)
            compressed_turn = Turn(
                turn_id=0,  # Special ID for compressed/summary
                user_message=Message(role="system", content=f"[Compressed History]\n{summary}"),
                checkpoint_hash="compressed"
            )
        else:
            compressed_turn = None
        
        # Rebuild turns list
        new_turns = [keep_first]
        if compressed_turn:
            new_turns.append(compressed_turn)
        new_turns.extend(keep_recent)
        
        self.turns = new_turns
        self._create_checkpoint("compression")
    
    def _summarize_turns(self, turns: List[Turn]) -> str:
        """Create semantic summary of multiple turns."""
        summary_parts = []
        for turn in turns:
            user_preview = turn.user_message.content[:100]
            if turn.assistant_message:
                assistant_preview = turn.assistant_message.content[:100]
                summary_parts.append(f"Turn {turn.turn_id}: {user_preview} -> {assistant_preview}")
            else:
                summary_parts.append(f"Turn {turn.turn_id}: {user_preview} [no response]")
        return f"{len(turns)} turns summarized. Key actions: " + "; ".join(summary_parts)
    
    def _create_checkpoint(self, reason: str = "manual") -> Optional[Path]:
        """Create a checkpoint for handoff continuity."""
        checkpoint = {
            "timestamp": time.time(),
            "reason": reason,
            "turn_counter": self.turn_counter,
            "metadata": self._checkpoint_metadata,
            "turns": [t.to_dict() for t in self.turns[-5:]]  # Keep last 5 turns for recovery
        }
        
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{int(time.time())}.json"
        try:
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint, f, indent=2)
            self._checkpoint_metadata["last_checkpoint"] = checkpoint_file.name
            return checkpoint_file
        except Exception as e:
            print(f"[CONTEXT] Checkpoint failed: {e}", file=__import__('sys').stderr)
            return None
    
    def load_checkpoint(self, checkpoint_file: Path) -> bool:
        """Load from a checkpoint for continuity."""
        try:
            with open(checkpoint_file) as f:
                data = json.load(f)
            
            self.turn_counter = data.get("turn_counter", 0)
            self._checkpoint_metadata = data.get("metadata", {})
            
            loaded_turns = []
            for turn_data in data.get("turns", []):
                turn = Turn(
                    turn_id=turn_data["turn_id"],
                    user_message=Message.from_dict(turn_data["user_message"]),
                    checkpoint_hash=turn_data.get("checkpoint_hash")
                )
                if turn_data.get("assistant_message"):
                    turn.assistant_message = Message.from_dict(turn_data["assistant_message"])
                turn.tool_calls = turn_data.get("tool_calls", [])
                loaded_turns.append(turn)
            
            self.turns = loaded_turns
            return True
        except Exception as e:
            print(f"[CONTEXT] Load checkpoint failed: {e}", file=__import__('sys').stderr)
            return False
    
    def get_context_for_llm(self) -> Tuple[List[Dict], int]:
        """
        Get formatted context ready for LLM consumption.
        Returns (messages, estimated_tokens).
        """
        messages = []
        total_tokens = 0
        
        for turn in self.turns:
            messages.append(turn.user_message.to_dict())
            total_tokens += self._estimate_message_tokens(turn.user_message)
            
            if turn.assistant_message:
                messages.append(turn.assistant_message.to_dict())
                total_tokens += self._estimate_message_tokens(turn.assistant_message)
            
            # Include tool calls as assistant message with tool calls
            if turn.tool_calls and turn.assistant_message:
                for tc in turn.tool_calls:
                    messages.append({
                        "role": "tool",
                        "content": f"Tool {tc['tool']}: {tc['output']}",
                        "tool_call_id": tc.get("tool", "unknown")
                    })
        
        return messages, total_tokens
    
    def get_recent_history(self, n_turns: int = 5) -> List[Dict]:
        """Get recent N turns as dict."""
        return [t.to_dict() for t in self.turns[-n_turns:]]
    
    def get_statistics(self) -> Dict:
        """Get context manager statistics."""
        return {
            "total_turns": self.turn_counter,
            "stored_turns": len(self.turns),
            "estimated_tokens": self._estimate_total_tokens(),
            "compression_events": self._checkpoint_metadata.get("compression_events", 0),
            "last_checkpoint": self._checkpoint_metadata.get("last_checkpoint"),
            "compression_ratio": self._estimate_total_tokens() / self.available_tokens if self.available_tokens > 0 else 0
        }


if __name__ == "__main__":
    # Test context manager
    cm = ContextManager(max_tokens=64000, reserve_tokens=4096)
    
    cm.start_turn("Hello, how are you?")
    cm.add_assistant_response("I'm doing well, thank you for asking!")
    cm.end_turn()
    
    cm.start_turn("Tell me about Python.")
    cm.add_assistant_response("Python is a programming language known for its simplicity.")
    cm.add_tool_call("web_search", {"query": "python programming"}, "Python is a high-level language...")
    cm.end_turn()
    
    stats = cm.get_statistics()
    print(f"Context Manager Test")
    print(f"  Turns: {stats['total_turns']}")
    print(f"  Est. Tokens: {stats['estimated_tokens']}")
    print(f"  Compression Events: {stats['compression_events']}")
