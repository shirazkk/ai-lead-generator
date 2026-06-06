"""
Prompt Engineering Module for AI Lead Generator
Exports optimized prompts for Gemini AI agents.
"""

from backend.prompts.analyzer_prompt import ANALYZER_PROMPT
from backend.prompts.outreach_prompt import OUTREACH_PROMPT

__all__ = [
    "ANALYZER_PROMPT",
    "OUTREACH_PROMPT",
]
