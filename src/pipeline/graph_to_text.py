from typing import Dict, List, Optional
from openai import OpenAI
from ..models.ttng import TTNGModel, Node, OrganizingAttribute
from ..models.narrative_context import NarrativeContext
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

class GraphToTextPipeline:
    """Pipeline for generating narrative text from TTNG following the paper's architecture"""
    
    def __init__(self, model: TTNGModel):
        self.model = model
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        
        # Store previous node references for context
        self.previous_nodes: Dict[str, str] = {}
        
    def craft_narrative_context(self, organizing_attribute: Optional[OrganizingAttribute] = None) -> Dict[str, List[str]]:
        """Component 1: Crafter - Initialize narrative space with available attributes"""
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
        
        # If organizing attribute is specified, prioritize those attributes
        if organizing_attribute:
            if organizing_attribute == OrganizingAttribute.ENTITY:
                context['entities'] = self._expand_entities(context['entities'])
            elif organizing_attribute == OrganizingAttribute.EVENT:
                context['events'] = self._expand_events(context['events'])
            elif organizing_attribute == OrganizingAttribute.TOPIC:
                context['topics'] = self._expand_topics(context['topics'])
        
        return context

    def calculate_time_periods(self, num_timepoints: int, base_time: Optional[datetime] = None) -> List[datetime]:
        """Calculate time intervals for narrative segments"""
        if base_time is None:
            base_time = datetime.now()
        
        # Create evenly spaced timepoints
        return [base_time + timedelta(days=i) for i in range(num_timepoints)]

    def map_attributes(self, node_id: str, context: Dict[str, List[str]], 
                      previous_node: Optional[str] = None) -> NarrativeContext:
        """Component 2: Cartographer - Map attributes to nodes maintaining continuity"""
        track_id = int(node_id.split('_')[1].replace('track', ''))
        timepoint = int(node_id.split('_')[0].replace('t', ''))
        
        # If there's a previous node, ensure attribute continuity
        if previous_node and previous_node in self.model.nodes:
            prev_attrs = self.model.nodes[previous_node].attributes
            # Maintain at least one shared attribute based on organizing attribute
            if self.model.organizing_attribute == OrganizingAttribute.ENTITY:
                entities = [random.choice(prev_attrs.entities)]
                events = [random.choice(context['events'])]
                topics = [random.choice(context['topics'])]
            elif self.model.organizing_attribute == OrganizingAttribute.EVENT:
                entities = [random.choice(context['entities'])]
                events = [random.choice(prev_attrs.events)]
                topics = [random.choice(context['topics'])]
            else:  # TOPIC
                entities = [random.choice(context['entities'])]
                events = [random.choice(context['events'])]
                topics = [random.choice(prev_attrs.topics)]
        else:
            # Select attributes based on track and maintain track coherence
            entities = [context['entities'][track_id % len(context['entities'])]]
            events = [context['events'][track_id % len(context['events'])]]
            topics = [context['topics'][track_id % len(context['topics'])]]
        
        # Store reference for future continuity
        self.previous_nodes[node_id] = previous_node if previous_node else node_id
        
        return NarrativeContext(
            entities=entities,
            events=events,
            topics=topics
        )

    def generate_text(self, node: Node, style: dict = None) -> str:
        """Component 3: Writer - Generate coherent narrative text"""
        try:
            # Get previous node in the same track for context
            track_nodes = [n for n in self.model.nodes.values() if n.track_id == node.track_id]
            track_nodes.sort(key=lambda x: x.time)
            prev_node_idx = track_nodes.index(node) - 1 if node in track_nodes else -1
            prev_node = track_nodes[prev_node_idx] if prev_node_idx >= 0 else None

            # Create a context-aware prompt with style preferences
            prompt = self._create_narrative_prompt(node, prev_node, style)
            system_prompt = self._create_system_prompt(style)

            try:
                # Call OpenAI API with the latest client version
                completion = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7,
                    presence_penalty=0.3,  # Encourage diverse content
                    frequency_penalty=0.3,  # Reduce repetition
                    response_format={"type": "text"}  # Ensure text response
                )
                
                # Extract the generated text from the response
                return completion.choices[0].message.content.strip()

            except Exception as api_error:
                raise Exception(f"OpenAI API error: {str(api_error)}")

        except Exception as e:
            raise Exception(f"Error generating text: {str(e)}")

    def _create_system_prompt(self, style: dict = None) -> str:
        """Create a system prompt based on style preferences"""
        if not style:
            return "You are a professional storyteller creating coherent narrative sequences."

        narrative_style = style.get('narrative_style', 'journalistic')
        tone = style.get('tone', 'neutral')

        style_descriptions = {
            'journalistic': "Write in a clear, factual style focusing on the who, what, when, where, and why.",
            'analytical': "Present information with detailed analysis and logical connections.",
            'descriptive': "Use rich, vivid language to paint a detailed picture of events and situations.",
            'academic': "Write in a formal, scholarly tone with precise terminology and structured arguments."
        }

        tone_descriptions = {
            'neutral': "Maintain an objective and balanced perspective.",
            'optimistic': "Emphasize positive developments and potential opportunities.",
            'critical': "Examine challenges and potential issues with careful scrutiny.",
            'balanced': "Present multiple perspectives while maintaining objectivity."
        }

        return f"""You are a professional storyteller specializing in {narrative_style} writing.
{style_descriptions.get(narrative_style, '')}
{tone_descriptions.get(tone, '')}
Focus on creating coherent narrative sequences that maintain continuity."""

    def _create_narrative_prompt(self, node: Node, prev_node: Optional[Node] = None, style: dict = None) -> str:
        """Create a context-aware prompt for text generation"""
        narrative_style = style.get('narrative_style', 'journalistic') if style else 'journalistic'
        
        style_prompts = {
            'journalistic': f"Write a news-style paragraph about {node.attributes.topics[0]} involving {node.attributes.entities[0]} and a {node.attributes.events[0]}.",
            'analytical': f"Analyze the implications of a {node.attributes.events[0]} in {node.attributes.topics[0]}, focusing on {node.attributes.entities[0]}.",
            'descriptive': f"Describe in detail how {node.attributes.entities[0]} is involved in a {node.attributes.events[0]} related to {node.attributes.topics[0]}.",
            'academic': f"Examine the significance of {node.attributes.entities[0]}'s involvement in a {node.attributes.events[0]} within the context of {node.attributes.topics[0]}."
        }

        prompt = style_prompts.get(narrative_style, style_prompts['journalistic'])
        prompt += "\nMaintain a professional and coherent narrative."

        if prev_node:
            prompt += f"\nEnsure continuity with the previous event involving {prev_node.attributes.entities[0]}."

        prompt += "\nKeep the response under 100 words while preserving key details and maintaining the specified tone."
        return prompt

    def _expand_entities(self, base_entities: List[str]) -> List[str]:
        """Expand entity list with more specific examples"""
        expanded = []
        for entity in base_entities:
            if entity == "Companies":
                expanded.extend(["Tech Startups", "Fortune 500 Companies", "Small Businesses"])
            elif entity == "Politicians":
                expanded.extend(["World Leaders", "Local Officials", "Policy Makers"])
            else:
                expanded.append(entity)
        return expanded

    def _expand_events(self, base_events: List[str]) -> List[str]:
        """Expand event list with more specific examples"""
        expanded = []
        for event in base_events:
            if event == "Product Launch":
                expanded.extend(["Major Product Release", "Beta Launch", "Market Entry"])
            elif event == "Policy Change":
                expanded.extend(["Regulation Update", "Law Enactment", "Policy Reform"])
            else:
                expanded.append(event)
        return expanded

    def _expand_topics(self, base_topics: List[str]) -> List[str]:
        """Expand topic list with more specific examples"""
        expanded = []
        for topic in base_topics:
            if topic == "Technology":
                expanded.extend(["AI Development", "Cybersecurity", "Digital Transformation"])
            elif topic == "Environment":
                expanded.extend(["Climate Change", "Renewable Energy", "Conservation"])
            else:
                expanded.append(topic)
        return expanded