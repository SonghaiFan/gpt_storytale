from dataclasses import dataclass

@dataclass
class StyleConfig:
    """Configuration for text generation style"""
    cefr_level: str = 'A1'
    tone: str = 'neutral'
    
    def __post_init__(self):
        valid_cefr_levels = {'A1', 'A2', 'B1', 'B2', 'C1'}
        valid_tones = {'neutral', 'optimistic', 'critical', 'balanced'}
        
        if self.cefr_level not in valid_cefr_levels:
            raise ValueError(f"Invalid CEFR level. Must be one of: {valid_cefr_levels}")
        if self.tone not in valid_tones:
            raise ValueError(f"Invalid tone. Must be one of: {valid_tones}") 