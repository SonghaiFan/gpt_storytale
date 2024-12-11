from typing import Dict, List, Optional, Any
from ...models.ttng import OrganizingAttribute

class NarrativeContextManager:
    """Manages narrative context and attribute mapping"""
    
    def __init__(self):
        self._base_context = {
            'topics': [
                'Technology', 'Politics', 'Environment', 'Business', 
                'Healthcare', 'Education', 'Science'
            ],
            'events': [
                'Product Launch', 'Policy Change', 'Natural Disaster',
                'Merger', 'Research Breakthrough', 'Market Shift'
            ],
            'entities': [
                'Companies', 'Politicians', 'Organizations', 'Researchers',
                'Institutions', 'Communities', 'Products'
            ]
        }
    
    def get_context(self, organizing_attribute: Optional[OrganizingAttribute] = None) -> Dict[str, List[str]]:
        """Get narrative context with optional attribute expansion"""
        context = self._base_context.copy()
        
        if organizing_attribute:
            if organizing_attribute == OrganizingAttribute.ENTITY:
                context['entities'] = self._expand_entities(context['entities'])
            elif organizing_attribute == OrganizingAttribute.EVENT:
                context['events'] = self._expand_events(context['events'])
            elif organizing_attribute == OrganizingAttribute.TOPIC:
                context['topics'] = self._expand_topics(context['topics'])
        
        return context
    
    @staticmethod
    def _expand_entities(base_entities: List[str]) -> List[str]:
        """Expand entity list with specific examples"""
        expansions = {
            "Companies": ["Tech Startups", "Fortune 500 Companies", "Small Businesses"],
            "Politicians": ["World Leaders", "Local Officials", "Policy Makers"]
        }
        return [exp for entity in base_entities for exp in expansions.get(entity, [entity])]
    
    @staticmethod
    def _expand_events(base_events: List[str]) -> List[str]:
        """Expand event list with specific examples"""
        expansions = {
            "Product Launch": ["Major Product Release", "Beta Launch", "Market Entry"],
            "Policy Change": ["Regulation Update", "Law Enactment", "Policy Reform"]
        }
        return [exp for event in base_events for exp in expansions.get(event, [event])]
    
    @staticmethod
    def _expand_topics(base_topics: List[str]) -> List[str]:
        """Expand topic list with specific examples"""
        expansions = {
            "Technology": ["AI Development", "Cybersecurity", "Digital Transformation"],
            "Environment": ["Climate Change", "Renewable Energy", "Conservation"]
        }
        return [exp for topic in base_topics for exp in expansions.get(topic, [topic])] 
    
    def initialize_narrative_space(self, story_config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Initialize narrative space from configuration or default values"""
        # First try to use provided configuration
        if story_config and 'timepoints' in story_config:
            context = self._extract_context_from_config(story_config)
        else:
            # Fallback to base context
            context = self._base_context.copy()
            
        # Ensure minimum required attributes
        for key in ['topics', 'events', 'entities']:
            if not context.get(key):
                context[key] = self._base_context[key]
                
        return context
        
    def _extract_context_from_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract unique attributes from story configuration"""
        context = {
            'topics': set(),
            'events': set(),
            'entities': set()
        }
        
        for timepoint in config['timepoints']:
            for track_data in timepoint['nodes'].values():
                context['topics'].update(track_data.get('topics', []))
                context['events'].update(track_data.get('events', []))
                context['entities'].update(track_data.get('entities', []))
                
        return {k: list(v) for k, v in context.items()} 