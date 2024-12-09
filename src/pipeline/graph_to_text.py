from typing import Dict, List
import openai
from ..models.ttng import TTNGModel, Node
from ..models.narrative_context import NarrativeContext
import os
from dotenv import load_dotenv

class GraphToTextPipeline:
    """Pipeline for generating narrative text from TTNG"""
    
    def __init__(self, model: TTNGModel):
        self.model = model
        load_dotenv()  # Load environment variables
        # Explicitly set OpenAI API key
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
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
        # Select attributes based on track and maintain continuity
        track_id = int(node_id.split('_')[1].replace('track', ''))
        
        # Select attributes based on track
        entities = [context['entities'][track_id % len(context['entities'])]]
        events = [context['events'][track_id % len(context['events'])]]
        topics = [context['topics'][track_id % len(context['topics'])]]
        
        return NarrativeContext(
            entities=entities,
            events=events,
            topics=topics
        )

    def generate_text(self, node: Node) -> str:
        """Generate narrative text for a node using OpenAI API"""
        try:
            # Create a prompt based on the node's context
            prompt = f"""Generate a short narrative paragraph about {node.attributes.topics[0]} 
            involving {node.attributes.entities[0]} and a {node.attributes.events[0]}.
            The story should be coherent and engaging, focusing on these elements while maintaining
            a professional tone. Keep it under 100 words."""

            # Call OpenAI API with explicit organization
            client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional storyteller creating coherent narrative sequences."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )

            # Extract and return the generated text
            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"Error generating text: {str(e)}")

    def _select_entities(self, track_id: str, context: Dict[str, List[str]]) -> List[str]:
        """Helper method to select entities for a track"""
        track_num = int(track_id)
        return [context['entities'][track_num % len(context['entities'])]]
    
    def _select_events(self, track_id: str, context: Dict[str, List[str]]) -> List[str]:
        """Helper method to select events for a track"""
        track_num = int(track_id)
        return [context['events'][track_num % len(context['events'])]]
    
    def _select_topics(self, track_id: str, context: Dict[str, List[str]]) -> List[str]:
        """Helper method to select topics for a track"""
        track_num = int(track_id)
        return [context['topics'][track_num % len(context['topics'])]]