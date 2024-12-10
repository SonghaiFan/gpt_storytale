from typing import Dict, List, Optional, Any
from openai import OpenAI
from ..models.ttng import TTNGModel, Node, OrganizingAttribute
from ..models.narrative_context import NarrativeContext
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import logging
from .components import (
    StyleConfig,
    NarrativeContextManager,
    PromptManager,
    GraphVisualizer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GraphToTextPipeline:
    """Pipeline for generating narrative text from TTNG"""
    
    def __init__(self, model: TTNGModel):
        self.model = model
        self.context_manager = NarrativeContextManager()
        self.prompt_manager = PromptManager()
        self.previous_nodes: Dict[str, str] = {}
        
        # Initialize OpenAI client
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)
    
    def craft_narrative_context(self, organizing_attribute: Optional[OrganizingAttribute] = None) -> Dict[str, List[str]]:
        """Initialize narrative space with available attributes"""
        return self.context_manager.get_context(organizing_attribute)
    
    def calculate_time_periods(self, num_timepoints: int, base_time: Optional[datetime] = None) -> List[datetime]:
        """Calculate time intervals for narrative segments"""
        base_time = base_time or datetime.now()
        return [base_time + timedelta(days=i) for i in range(num_timepoints)]
    
    def map_attributes(self, node_id: str, context: Dict[str, List[str]], 
                      previous_node: Optional[str] = None,
                      provided_attributes: Optional[Dict[str, List[str]]] = None) -> NarrativeContext:
        """Map attributes to nodes maintaining continuity"""
        if provided_attributes:
            # Use provided attributes if available
            attrs = {
                'entities': provided_attributes.get('entities', []),
                'events': provided_attributes.get('events', []),
                'topics': provided_attributes.get('topics', [])
            }
        else:
            # Otherwise, generate attributes
            track_id = int(node_id.split('_')[1].replace('track', ''))
            
            if previous_node and previous_node in self.model.nodes:
                attrs = self._get_continuous_attributes(previous_node, context)
            else:
                attrs = self._get_new_attributes(track_id, context)
        
        self.previous_nodes[node_id] = previous_node or node_id
        return NarrativeContext(**attrs)
    
    def generate_text(self, node: Node, style: Optional[Dict[str, str]] = None) -> str:
        """Generate coherent narrative text"""
        try:
            style_config = StyleConfig(**style) if style else StyleConfig()
            prev_node = self._get_previous_node(node)
            
            system_prompt = self.prompt_manager.create_system_prompt(style_config)
            user_prompt = self.prompt_manager.create_narrative_prompt(node, prev_node, style_config)
            
            return self._generate_completion(system_prompt, user_prompt)
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise
    
    def visualize_story_graph(self, output_path: Optional[str] = None, show: bool = True) -> None:
        """Visualize the story graph structure"""
        GraphVisualizer.visualize(self.model, output_path, show)
    
    def export_graph_data(self, output_path: str) -> None:
        """Export the graph data as JSON"""
        GraphVisualizer.export_json(self.model, output_path)
    
    def _get_continuous_attributes(self, prev_node: str, context: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Get attributes maintaining continuity with previous node"""
        prev_attrs = self.model.nodes[prev_node].attributes
        
        if self.model.organizing_attribute == OrganizingAttribute.ENTITY:
            return {
                'entities': [random.choice(prev_attrs.entities)],
                'events': [random.choice(context['events'])],
                'topics': [random.choice(context['topics'])]
            }
        elif self.model.organizing_attribute == OrganizingAttribute.EVENT:
            return {
                'entities': [random.choice(context['entities'])],
                'events': [random.choice(prev_attrs.events)],
                'topics': [random.choice(context['topics'])]
            }
        else:  # TOPIC
            return {
                'entities': [random.choice(context['entities'])],
                'events': [random.choice(context['events'])],
                'topics': [random.choice(prev_attrs.topics)]
            }
    
    def _get_new_attributes(self, track_id: int, context: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Get new attributes based on track"""
        return {
            'entities': [context['entities'][track_id % len(context['entities'])]],
            'events': [context['events'][track_id % len(context['events'])]],
            'topics': [context['topics'][track_id % len(context['topics'])]]
        }
    
    def _get_previous_node(self, node: Node) -> Optional[Node]:
        """Get previous node in the same track"""
        track_nodes = [n for n in self.model.nodes.values() if n.track_id == node.track_id]
        track_nodes.sort(key=lambda x: x.time)
        prev_node_idx = track_nodes.index(node) - 1 if node in track_nodes else -1
        return track_nodes[prev_node_idx] if prev_node_idx >= 0 else None
    
    def _generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text completion using OpenAI API"""
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3,
                response_format={"type": "text"}
            )
            
            text = completion.choices[0].message.content.strip()
            words = text.split()
            return ' '.join(words[:120]) + ('...' if len(words) > 120 else '')
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise