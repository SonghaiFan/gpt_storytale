from dataclasses import dataclass
from typing import List

@dataclass
class NarrativeContext:
    """Represents the fundamental narrative elements (NCEs)"""
    entities: List[str]  # Distinct individuals, objects, locations, organizations
    events: List[str]    # Significant occurrences involving entities
    topics: List[str]    # Overarching subjects connecting entities and events 