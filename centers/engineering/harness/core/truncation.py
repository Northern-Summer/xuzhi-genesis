"""
Observation Truncator - SWE-agent inspired
==========================================
Inspired by SWE-agent's observation truncation system.

Provides character-level truncation with informative placeholders
to prevent context overflow while preserving debugging ability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TruncationResult:
    """Result of a truncation operation"""
    text: str
    original_length: int
    truncated_length: int
    was_truncated: bool
    elided_chars: int = 0


class ObservationTruncator:
    """
    Truncate long observations to a maximum character length.
    
    Inspired by SWE-agent's next_step_truncated_observation_template:
    
    ```
    Observation: {{observation[:max_observation_length]}}<response clipped>
    <NOTE>Observations should not exceeded {{max_observation_length}} characters.
    {{elided_chars}} characters were elided. Please try a different command that
    produces less output or use head/tail/grep/redirect the output to a file.
    Do not use interactive pagers.</NOTE>
    ```
    
    Features:
    - Character-level truncation
    - Preserves beginning of output (usually contains the command context)
    - Adds informative clip notice
    - Supports different truncation strategies
    """
    
    DEFAULT_MAX_LENGTH = 100_000  # Matches SWE-agent
    CLIP_NOTICE = "<response clipped>"
    NOTE_TEMPLATE = (
        "\n<NOTE>Output truncated. "
        "{elided_chars} characters were elided. "
        "Consider using: head, tail, grep, or redirect to file (> output.txt). "
        "Avoid interactive pagers (less, more). "
        "Original length: {original_length} chars.</NOTE>"
    )
    
    def __init__(
        self,
        max_length: int = DEFAULT_MAX_LENGTH,
        include_clip_notice: bool = True,
        include_note: bool = True,
        preserve_end: bool = False,
        truncation_target: str = "observation"
    ):
        """
        Args:
            max_length: Maximum characters in output (0 = no limit)
            include_clip_notice: Include the <response clipped> marker
            include_note: Include the helpful NOTE with suggestions
            preserve_end: If True, preserve end of output instead of beginning
            truncation_target: Target name for error messages ("observation", "stdout", etc.)
        """
        self.max_length = max_length
        self.include_clip_notice = include_clip_notice
        self.include_note = include_note
        self.preserve_end = preserve_end
        self.truncation_target = truncation_target
    
    def truncate(self, text: str) -> TruncationResult:
        """
        Truncate text if it exceeds max_length.
        
        Args:
            text: The text to potentially truncate
            
        Returns:
            TruncationResult with truncated text and metadata
        """
        original_length = len(text)
        
        if self.max_length <= 0 or original_length <= self.max_length:
            return TruncationResult(
                text=text,
                original_length=original_length,
                truncated_length=original_length,
                was_truncated=False,
                elided_chars=0
            )
        
        # Perform truncation
        if self.preserve_end:
            # Keep end (useful for error messages that end with the error)
            start_text = text[:self.max_length // 4]
            end_text = text[original_length - self.max_length + len(start_text):]
            truncated = start_text + "\n... [middle omitted] ...\n" + end_text
        else:
            # Keep beginning (default - context is usually at start)
            truncated = text[:self.max_length]
        
        # Build clip notice
        elided_chars = original_length - len(truncated)
        parts = []
        
        if self.include_clip_notice:
            parts.append(self.CLIP_NOTICE)
        
        if self.include_note:
            note = self.NOTE_TEMPLATE.format(
                elided_chars=elided_chars,
                original_length=original_length
            )
            parts.append(note)
        
        truncated = truncated + "\n" + "\n".join(parts)
        
        return TruncationResult(
            text=truncated,
            original_length=original_length,
            truncated_length=len(truncated),
            was_truncated=True,
            elided_chars=elided_chars
        )
    
    def truncate_with_template(
        self,
        text: str,
        template: Optional[str] = None
    ) -> str:
        """
        Truncate and format with a custom Jinja2-style template.
        
        Template variables:
            - {{observation}}: The (truncated) observation text
            - {{max_observation_length}}: The max_length setting
            - {{elided_chars}}: Number of characters removed
            - {{original_length}}: Original text length
        """
        result = self.truncate(text)
        
        if template is None:
            return result.text
        
        return template.format(
            observation=result.text,
            max_observation_length=self.max_length,
            elided_chars=result.elided_chars,
            original_length=result.original_length
        )


class MultiModalTruncator(ObservationTruncator):
    """
    Truncator for multimodal content (text + images).
    
    In addition to text truncation, can limit number of images
    and provide summaries for image-heavy content.
    """
    
    def __init__(
        self,
        max_length: int = 100_000,
        max_images: int = 10,
        image_summary_length: int = 500,
        **kwargs
    ):
        super().__init__(max_length=max_length, **kwargs)
        self.max_images = max_images
        self.image_summary_length = image_summary_length
    
    def truncate_content(self, content: list[dict]) -> list[dict]:
        """
        Truncate a multimodal content list (text + images).
        
        Args:
            content: List of content items with 'type' ('text' or 'image_url')
            
        Returns:
            Truncated content list
        """
        if not content:
            return content
        
        text_items = [c for c in content if c.get("type") == "text"]
        image_items = [c for c in content if c.get("type") == "image_url"]
        
        # Truncate text
        result_texts = []
        total_text_length = 0
        
        for item in text_items:
            text = item.get("text", "")
            if total_text_length + len(text) > self.max_length:
                remaining = self.max_length - total_text_length
                if remaining > 100:  # Only add if meaningful
                    result_texts.append({
                        **item,
                        "text": text[:remaining] + f"\n<text truncated, {len(text) - remaining} chars omitted>"
                    })
                break
            result_texts.append(item)
            total_text_length += len(text)
        
        # Limit images
        result_images = image_items[:self.max_images]
        if len(image_items) > self.max_images:
            result_images.append({
                "type": "text",
                "text": f"<{len(image_items) - self.max_images} images omitted - too many images>"
            })
        
        # Interleave: texts first, then images
        return result_texts + result_images


class BashOutputTruncator(ObservationTruncator):
    """
    Specialized truncator for bash command output.
    
    Optimized for command-line output patterns:
    - Preserves first few lines (command context)
    - Preserves last few lines (often error/summary)
    - Marks middle as omitted
    - Provides helpful suggestions for reducing output
    """
    
    PRESERVE_LINES_START = 50
    PRESERVE_LINES_END = 30
    
    def truncate_bash_output(self, output: str, stderr: str = "") -> str:
        """
        Truncate bash output intelligently.
        
        Args:
            output: stdout content
            stderr: stderr content (prepended to output)
            
        Returns:
            Truncated and formatted output
        """
        # Combine with clear separator
        if stderr:
            combined = f"[STDERR]\n{stderr}\n[STDOUT]\n{output}"
        else:
            combined = output
        
        lines = combined.split("\n")
        total_lines = len(lines)
        
        if total_lines <= self.PRESERVE_LINES_START + self.PRESERVE_LINES_END:
            return self.truncate(combined).text
        
        # Preserve start and end
        start = "\n".join(lines[:self.PRESERVE_LINES_START])
        end = "\n".join(lines[-self.PRESERVE_LINES_END:])
        omitted = total_lines - self.PRESERVE_LINES_START - self.PRESERVE_LINES_END
        
        truncated = (
            start
            + f"\n\n... {omitted} lines omitted ...\n\n"
            + end
        )
        
        result = self.truncate(truncated)
        
        if not result.was_truncated:
            # Even the preserved lines are within limit
            return result.text
        
        # Still too long - fallback to simple truncation
        return self.truncate(output[:self.max_length // 2] + "\n...\n" + output[-self.max_length // 2:]).text


class ErrorAwareTruncator(ObservationTruncator):
    """
    Truncator that is aware of common error patterns.
    
    Tries to preserve error messages and stack traces while
    truncating repetitive or verbose output.
    """
    
    ERROR_PATTERNS = [
        "Error:",
        "Exception:",
        "Traceback (most recent call last):",
        "  File ",
        "FAILED",
        "AssertionError",
    ]
    
    def truncate_with_error_focus(self, text: str) -> str:
        """
        Truncate text while trying to preserve error information.
        
        Strategy:
        1. Find error indicators
        2. If error found, preserve context around it
        3. Otherwise fall back to standard truncation
        """
        error_indices = []
        for pattern in self.ERROR_PATTERNS:
            start = 0
            while True:
                idx = text.find(pattern, start)
                if idx == -1:
                    break
                error_indices.append(idx)
                start = idx + 1
        
        if not error_indices:
            return self.truncate(text).text
        
        # Find the most important error (usually first)
        primary_error_idx = min(error_indices)
        
        # Calculate how much we can preserve
        preserve_start = max(0, primary_error_idx - 2000)
        preserve_end = min(len(text), primary_error_idx + 5000)
        
        # Build truncated text with error preserved
        before_error = text[preserve_start:primary_error_idx]
        error_region = text[primary_error_idx:preserve_end]
        after_available = self.max_length - len(before_error) - len(error_region) - 200
        
        if after_available > 0 and preserve_end < len(text):
            after = text[preserve_end:preserve_end + after_available]
        else:
            after = ""
        
        truncated = (
            (f"[... {preserve_start} chars before error omitted ...]\n" if preserve_start > 0 else "")
            + before_error
            + error_region
            + (f"\n[... {len(text) - preserve_end} chars after error omitted ...]" if preserve_end < len(text) and not after else "")
            + after
        )
        
        result = self.truncate(truncated)
        return result.text


# Convenience function
def truncate_observation(
    text: str,
    max_length: int = 100_000,
    truncate_type: str = "standard"
) -> str:
    """
    Convenience function for common truncation needs.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        truncate_type: 'standard', 'bash', 'error', 'multimodal'
    """
    if truncate_type == "bash":
        truncator = BashOutputTruncator(max_length=max_length)
        return truncator.truncate(text).text
    elif truncate_type == "error":
        truncator = ErrorAwareTruncator(max_length=max_length)
        return truncator.truncate_with_error_focus(text)
    else:
        truncator = ObservationTruncator(max_length=max_length)
        return truncator.truncate(text).text
