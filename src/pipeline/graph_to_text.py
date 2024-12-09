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

            # Create prompts
            system_prompt = self._create_system_prompt(style)
            user_prompt = self._create_narrative_prompt(node, prev_node, style)

            try:
                # Call OpenAI API with the latest client version
                completion = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=200,  # Increased for headline and formatting
                    temperature=0.7,
                    presence_penalty=0.3,  # Encourage diverse content
                    frequency_penalty=0.3,  # Reduce repetition
                    response_format={"type": "text"}  # Ensure text response
                )
                
                # Extract and clean the generated text
                text = completion.choices[0].message.content.strip()
                
                # Ensure the text is not too long (aim for ~100 words)
                words = text.split()
                if len(words) > 120:  # Allow some flexibility
                    text = ' '.join(words[:100]) + '...'
                
                return text

            except Exception as api_error:
                raise Exception(f"OpenAI API error: {str(api_error)}")

        except Exception as e:
            raise Exception(f"Error generating text: {str(e)}")

    def _create_system_prompt(self, style: dict = None) -> str:
        """Create a system prompt based on style preferences"""
        base_prompt = """You are a senior reporter for The New York Times, tasked with writing fictional news reports 
        that form a coherent narrative sequence. Your writing should be:
        - Concise and clear, using plain English
        - Logically connected between segments with intriguing continuity
        - Approximately 100 words per segment (1-minute read)
        - Subtle in theme integration, avoiding explicit structural references"""

        if not style:
            return base_prompt

        cefr_level = style.get('cefr_level', 'A1')
        tone = style.get('tone', 'neutral')

        cefr_guidelines = {
            'A1': """
            - Use very basic phrases and everyday vocabulary
            - Write simple, short sentences
            - Focus on concrete, familiar topics
            - Use present tense predominantly
            - Avoid complex grammar structures""",
            
            'A2': """
            - Use basic phrases and common vocabulary
            - Write simple but connected sentences
            - Include some simple past tense
            - Describe simple aspects of daily life
            - Use basic connectors (and, but, because)""",
            
            'B1': """
            - Use common everyday vocabulary
            - Connect ideas in a simple sequence
            - Include main tenses (present, past, future)
            - Describe experiences and events
            - Use common linking words effectively""",
            
            'B2': """
            - Use clear, detailed language
            - Express viewpoints and explain advantages/disadvantages
            - Use a range of linking words
            - Include some complex sentences
            - Maintain good grammatical control""",
            
            'C1': """
            - Use precise and natural language
            - Express ideas fluently and spontaneously
            - Use complex sentence structures
            - Include idiomatic expressions where appropriate
            - Maintain consistent grammatical control"""
        }

        tone_guidelines = {
            'neutral': "Report facts objectively without bias.",
            'optimistic': "Highlight constructive developments while staying factual.",
            'critical': "Examine issues carefully while remaining accessible.",
            'balanced': "Present multiple viewpoints in a clear, understandable way."
        }

        return f"""{base_prompt}
{cefr_guidelines.get(cefr_level, cefr_guidelines['A1'])}
{tone_guidelines.get(tone, tone_guidelines['neutral'])}"""

    def _create_narrative_prompt(self, node: Node, prev_node: Optional[Node] = None, style: dict = None) -> str:
        """Create a context-aware prompt for text generation"""
        # Format time period
        time_period = node.time.strftime("%B %d, %Y")
        
        # Get node ID and track information
        node_id = f"Node {node.track_id}"
        
        # Get CEFR level
        cefr_level = style.get('cefr_level', 'A1') if style else 'A1'
        
        # Build the prompt template
        prompt = f"""
        Chapter ID: {node_id}
        Time Period: {time_period}
        Topic: {node.attributes.topics[0]}
        Entity: {node.attributes.entities[0]}
        Event: {node.attributes.events[0]}
        Language Level: CEFR {cefr_level}
        
        Requirements:
        - Write a news report that incorporates all the elements above
        - Keep the language at CEFR {cefr_level} level
        - Aim for approximately 100 words
        - Make the theme strikingly prominent without explicitly stating it
        - Include all specified entities naturally in the story
        """

        # Add previous context if available
        if prev_node:
            prev_time = prev_node.time.strftime("%B %d, %Y")
            prompt += f"""
            Previous Context:
            Time: {prev_time}
            Entity: {prev_node.attributes.entities[0]}
            Event: {prev_node.attributes.events[0]}
            
            Ensure strong narrative continuity with the previous event while maintaining independence.
            """

        # Add CEFR-specific writing guidelines
        cefr_writing_tips = {
            'A1': "Use very simple sentences with basic present tense and common words.",
            'A2': "Use simple sentences with basic past tense and everyday vocabulary.",
            'B1': "Write clear sequences with common linking words and main tenses.",
            'B2': "Include some complex sentences and explain relationships between ideas.",
            'C1': "Use sophisticated language while maintaining clarity and natural flow."
        }

        prompt += f"""
        Writing Guidelines:
        {cefr_writing_tips.get(cefr_level, cefr_writing_tips['A1'])}
        Keep sentences {self._get_sentence_length_guide(cefr_level)}.
        Use vocabulary appropriate for {cefr_level} level.
        
        Write a clear, engaging news report following these guidelines."""

        return prompt

    def _get_sentence_length_guide(self, cefr_level: str) -> str:
        """Get sentence length guidelines based on CEFR level"""
        guides = {
            'A1': "very short (5-7 words)",
            'A2': "short (7-10 words)",
            'B1': "moderate (10-15 words)",
            'B2': "varied (10-20 words)",
            'C1': "natural and varied (no strict limit)"
        }
        return guides.get(cefr_level, guides['A1'])

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