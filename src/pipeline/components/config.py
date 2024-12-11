"""
Configuration classes for the pipeline components.
"""

from dataclasses import dataclass

@dataclass
class StyleConfig:
    """Configuration for text generation style"""
    cefr_level: str = 'B2'  # Default CEFR level
    tone: str = 'neutral'  # Default tone 