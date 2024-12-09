from typing import Dict, List
import openai
from ..models.ttng import TTNGModel, Node
from ..models.narrative_context import NarrativeContext

class GraphToTextPipeline:
    """Pipeline for generating narrative text from TTNG"""
    
    def __init__(self, model: TTNGModel):
        self.model = model
        
    def craft_narrative_context(self) -> Dict[str, List[str]]:
        """Step 1: Craft narrative context elements"""
        context = {
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
        return context
        
    def map_attributes(self, node_id: str, context: Dict[str, List[str]]) -> NarrativeContext:
        """Step 2: Map narrative attributes to nodes"""
        node = self.model.nodes[node_id]
        track_id = node.track_id
        
        # Select attributes based on track and maintain continuity
        entities = self._select_entities(track_id, context)
        events = self._select_events(track_id, context)
        topics = self._select_topics(track_id, context)
        
        return NarrativeContext(
            entities=entities,
            events=events,
            topics=topics
        )
    
    def generate_text(self, node: Node) -> str:
        """Step 3: Generate coherent news text for a node"""
        prompt = self._construct_prompt(node)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a news writer creating coherent narrative text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating text: {e}")
            return f"Error generating text for node with attributes: {node.attributes}"
    
    def _select_entities(self, track_id: str, context: Dict[str, List[str]]) -> List[str]:
        """Helper to select relevant entities for a track"""
        # Get connected nodes in the same track
        track_nodes = self.model.tracks.get(track_id, [])
        
        # Select entities based on track theme and existing connections
        selected = []
        for entity in context['entities']:
            if len(selected) >= 3:  # Limit to 3 entities per node
                break
            # Add logic here to select relevant entities based on track theme
            selected.append(entity)
        return selected
        
    def _select_events(self, track_id: str, context: Dict[str, List[str]]) -> List[str]:
        """Helper to select relevant events for a track"""
        # Similar to _select_entities but for events
        selected = []
        for event in context['events']:
            if len(selected) >= 2:  # Limit to 2 events per node
                break
            selected.append(event)
        return selected
        
    def _select_topics(self, track_id: str, context: Dict[str, List[str]]) -> List[str]:
        """Helper to select relevant topics for a track"""
        # Similar to _select_entities but for topics
        selected = []
        for topic in context['topics']:
            if len(selected) >= 2:  # Limit to 2 topics per node
                break
            selected.append(topic)
        return selected
        
    def _construct_prompt(self, node: Node) -> str:
        """Helper to construct LLM prompt"""
        entities = ", ".join(node.attributes.entities)
        events = ", ".join(node.attributes.events)
        topics = ", ".join(node.attributes.topics)
        
        prompt = f"""
        Generate a news article paragraph that incorporates the following elements:
        - Entities: {entities}
        - Events: {events}
        - Topics: {topics}
        
        The text should be coherent, factual in tone, and maintain narrative continuity.
        Time period: {node.time.strftime('%Y-%m-%d')}
        """
        return prompt 