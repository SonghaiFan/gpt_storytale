from typing import Dict, List, Optional, Any, Set
from openai import OpenAI
from ..models.ttng import TTNGModel, Node, OrganizingAttribute, NarrativeSpace
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
from .components import (
    StyleConfig,
    PromptManager,
    NarrativeSpaceManager
)
import json
from .components.logger_config import setup_logger

logger = setup_logger(__name__)

class GraphToTextPipeline:
    """Pipeline for generating narrative text from TTNG"""
    
    def __init__(self, model: TTNGModel):
        """Initialize pipeline with TTNG model and components"""
        self.model = model
        self.context_manager = NarrativeSpaceManager()
        self.prompt_manager = PromptManager()
        
        # Initialize OpenAI client
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        
        # Use TTNG's built-in validation
        self.model.validate_graph()
        
        logger.info("Initialized GraphToTextPipeline with model settings:")
        logger.info("Idiom: %s", model.idiom.value)
        logger.info("Organizing Attribute: %s", model.organizing_attribute.value)

    def initialize_story_attributes(self) -> Dict[str, List[str]]:
        """Initialize story attributes by generating narrative space"""
        # Get graph dimensions
        structure = self.model.get_graph_dimensions()
        
        # Generate narrative space using the manager
        return self.context_manager.initialize_story_attributes(structure)
    
    def calculate_time_periods(self, num_timepoints: int, base_time: Optional[datetime] = None) -> List[datetime]:
        """Calculate time intervals for narrative segments"""
        base_time = base_time or datetime.now()
        return [base_time + timedelta(days=i) for i in range(num_timepoints)]
    
    def map_attributes(self, node_id: str, context: Dict[str, List[str]], 
                      previous_node: Optional[str] = None,
                      provided_attributes: Optional[Dict[str, List[str]]] = None) -> NarrativeSpace:
        """Map attributes using TTNG's coherence rules"""
        if provided_attributes:
            return NarrativeSpace(**provided_attributes)
        
        # Use TTNG's direct track access instead of string manipulation
        node = self.model.nodes[node_id]
        track_id = node.track_id
        connected_tracks = self.model.get_track_connections(track_id)
        
        # Create mapping between uppercase and lowercase attribute names
        attr_mapping = {
            'ENTITY': 'entities',
            'EVENT': 'events',
            'TOPIC': 'topics'
        }
        
        attrs = {}
        for attr_type in ['entities', 'events', 'topics']:
            # Skip if the key doesn't exist in context
            if attr_type not in context:
                continue
                
            available = set(context[attr_type])
            organizing_attr = self.model.organizing_attribute.value
            if organizing_attr == attr_type.upper():
                # Use TTNG's track attribute management
                attrs[attr_type] = list(self.model.get_track_attributes(track_id))
            else:
                # Leverage TTNG's coherence validation
                for connected_track in connected_tracks:
                    track_nodes = self.model.tracks[connected_track]
                    for connected_node in track_nodes:
                        if self.model.validate_coherence(node_id, connected_node):
                            connected_attrs = self.model.get_track_attributes(connected_track)
                            available -= set(connected_attrs)
                attrs[attr_type] = [random.choice(list(available) or context[attr_type])]
        
        return NarrativeSpace(**attrs)
    
    def generate_text(self, node: Node, style: Optional[Dict[str, str]] = None) -> str:
        """Generate text with enhanced TTNG context awareness"""
        try:
            style_config = StyleConfig(**style) if style else StyleConfig()
            
            # Get node context from TTNG
            node_id = next(nid for nid, n in self.model.nodes.items() if n == node)
            track_id = node.track_id
            
            # Get structural context
            in_degree, out_degree = self.model.get_node_degree(node_id)
            connected_tracks = self.model.get_track_connections(track_id)
            track_attributes = self.model.get_track_attributes(track_id)
            
            # Create prompts without the extra context parameter
            system_prompt = self.prompt_manager.create_system_prompt(style_config)
            user_prompt = self.prompt_manager.create_narrative_prompt(
                node=node,
                prev_node=self.model.get_previous_node_in_track(node_id),
                style=style_config
            )
            
            return self._generate_completion(system_prompt, user_prompt)
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise
    
    
    def _get_previous_node(self, node: Node) -> Optional[Node]:
        """Get previous node using TTNG's graph structure"""
        node_id = next((nid for nid, n in self.model.nodes.items() if n == node), None)
        if not node_id:
            return None
        
        # Use TTNG's edge information directly
        incoming_edges = [edge[0] for edge in self.model.edges if edge[1] == node_id]
        return self.model.nodes[incoming_edges[0]] if incoming_edges else self.model.get_previous_node_in_track(node_id)
    
    def _generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text completion using OpenAI API"""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3,
                response_format={"type": "text"}
            )
            
            response_text = completion.choices[0].message.content.strip()
            # Log prompts sent to OpenAI
            logger.info("\nPrompts sent to OpenAI:")
            logger.info("System prompt:\n%s", system_prompt)
            logger.info("User prompt:\n%s", user_prompt)
            logger.info("\nOpenAI Response:\n%s", response_text)
            
            words = response_text.split()
            return ' '.join(words[:120]) + ('...' if len(words) > 120 else '')
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def generate_node_attributes(self) -> None:
        """Generate attributes for all nodes in the graph using LLM"""
        # Initialize context if not already done
        if not hasattr(self, '_context'):
            self._context = self.initialize_story_attributes()
        
        # Use TTNG's temporal ordering
        sorted_nodes = sorted(
            self.model.nodes.items(), 
            key=lambda x: (x[1].time_index, int(x[1].track_id))
        )
        
        for node_id, node in sorted_nodes:
            prev_node = self.model.get_previous_node_in_track(node_id)
            attributes = self.map_attributes(
                node_id, 
                self._context,
                prev_node.track_id if prev_node else None
            )
            node.attributes = attributes
    
    def analyze_narrative_structure(self) -> Dict[str, Any]:
        """Analyze narrative structure using TTNG's graph features"""
        dimensions = self.model.get_graph_dimensions()
        structure = {
            "dimensions": dimensions,
            "tracks": len(self.model.tracks),
            "connections": {}
        }
        
        # Analyze track connections
        for track_id in self.model.tracks:
            connections = self.model.get_track_connections(track_id)
            structure["connections"][track_id] = {
                "connected_tracks": connections,
                "attributes": list(self.model.get_track_attributes(track_id))
            }
        
        return structure
    
    def validate_narrative_coherence(self) -> bool:
        """Validate narrative coherence using TTNG's coherence rules"""
        try:
            for from_node, to_node in self.model.edges:
                if not self.model.validate_coherence(from_node, to_node):
                    logger.warning(f"Coherence violation between {from_node} and {to_node}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error validating coherence: {str(e)}")
            return False