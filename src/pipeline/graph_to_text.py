from typing import Dict, List, Optional, Any, Set
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
        """Enhanced attribute mapping with coherence rules"""
        track_id = int(node_id.split('_')[1].replace('track', ''))
        
        if provided_attributes:
            return NarrativeContext(**provided_attributes)
        
        # Get track's existing attributes
        track_attrs = self.model.get_track_attributes(str(track_id))
        
        # Get connected tracks' attributes
        connected_tracks = self.model.get_track_connections(str(track_id))
        connected_attrs = set()
        for t in connected_tracks:
            connected_attrs.update(self.model.get_track_attributes(t))
        
        # Select attributes ensuring track coherence and cross-track diversity
        attrs = {
            'entities': self._select_coherent_attributes('entities', track_attrs, connected_attrs, context),
            'events': self._select_coherent_attributes('events', track_attrs, connected_attrs, context),
            'topics': self._select_coherent_attributes('topics', track_attrs, connected_attrs, context)
        }
        
        return NarrativeContext(**attrs)
    
    def generate_text(self, node: Node, style: Optional[Dict[str, str]] = None) -> str:
        """Generate text with enhanced context awareness"""
        try:
            style_config = StyleConfig(**style) if style else StyleConfig()
            
            # Get narrative context
            prev_node = self._get_previous_node(node)
            track_context = self._get_track_context(node)
            temporal_context = self._get_temporal_context(node)
            
            # Create enhanced prompts
            system_prompt = self.prompt_manager.create_system_prompt(style_config)
            user_prompt = self.prompt_manager.create_narrative_prompt(
                node, 
                prev_node,
                style_config,
                track_context=track_context,
                temporal_context=temporal_context
            )
            
            return self._generate_completion(system_prompt, user_prompt)
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise
    
    
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
        """Get previous node based on graph edges or temporal order in same track"""
        node_id = None
        # Find the node ID from the model
        for nid, n in self.model.nodes.items():
            if n == node:
                node_id = nid
                break
        
        if not node_id:
            return None
        
        # First try to find parent node through edges
        for from_node, to_node in self.model.edges:
            if to_node == node_id:
                return self.model.nodes[from_node]
        
        # If no parent found through edges, fallback to temporal order in same track
        track_nodes = [n for n in self.model.nodes.values() if n.track_id == node.track_id]
        track_nodes.sort(key=lambda x: x.time)
        prev_node_idx = track_nodes.index(node) - 1 if node in track_nodes else -1
        return track_nodes[prev_node_idx] if prev_node_idx >= 0 else None
    
    def _generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text completion using OpenAI API"""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Log the prompts
            logger.info("Sending prompts to OpenAI for text generation:")
            logger.info("System prompt: %s", system_prompt)
            logger.info("User prompt: %s", user_prompt)
            
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3,
                response_format={"type": "text"}
            )
            
            # Log the response
            response_text = completion.choices[0].message.content.strip()
            logger.info("Received response from OpenAI:")
            logger.info(response_text)
            
            # Process and return the text
            words = response_text.split()
            return ' '.join(words[:120]) + ('...' if len(words) > 120 else '')
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _select_coherent_attributes(self, attr_type: str, 
                                  track_attrs: Set[str],
                                  connected_attrs: Set[str],
                                  context: Dict[str, List[str]]) -> List[str]:
        """Select attributes maintaining coherence rules"""
        if not track_attrs:  # If no existing attributes
            if self.model.organizing_attribute.value == attr_type:
                # For organizing attribute, select a new one
                return [random.choice(context[attr_type])]
            else:
                # For other attributes, can share with connected tracks
                available = set(context[attr_type]) - connected_attrs
                return [random.choice(list(available) or context[attr_type])]
                
        # If we have existing attributes
        if self.model.organizing_attribute.value == attr_type:
            # Must maintain track coherence for organizing attribute
            return list(track_attrs)
        else:
            # Can share with connected tracks but prefer diversity
            available = set(context[attr_type]) - connected_attrs
            return [random.choice(list(available) or context[attr_type])]
    
    def generate_node_attributes(self) -> None:
        """Generate attributes for all nodes in the graph using LLM"""
        # Get base narrative context
        context = self.context_manager.get_context(self.model.organizing_attribute)
        
        # Process nodes in temporal order
        sorted_nodes = sorted(self.model.nodes.items(), key=lambda x: x[1].time)
        
        for node_id, node in sorted_nodes:
            # Find previous node in same track
            prev_node = self._get_previous_node(node)
            
            # Generate attributes maintaining coherence
            attributes = self.map_attributes(node_id, context, 
                                          prev_node.track_id if prev_node else None)
            
            # Update node with generated attributes
            node.attributes = attributes