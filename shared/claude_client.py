"""
shared/claude_client.py
-----------------------
Backward-compatible import path for the course exercises.

The implementation now lives in shared.llm_client so the same ask() helper can
use Anthropic, OpenAI, or side-by-side comparison mode.
"""

from shared.llm_client import ask, compare

__all__ = ["ask", "compare"]
