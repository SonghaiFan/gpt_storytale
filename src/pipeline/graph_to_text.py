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
        base_prompt = """You are a senior hard news reporter for The New York Times, specializing in factual, 
        objective reporting of significant events. Your writing should follow these principles:
        - Use the inverted pyramid structure (most important information first)
        - Focus on facts, figures, and verifiable information
        - Maintain strict objectivity and journalistic neutrality
        - Emphasize the impact and significance of events
        - Connect local events to broader regional or global implications
        - Use authoritative and precise language
        - Follow AP style guidelines for news writing
        
        Key elements to include:
        - Strong, factual lead paragraph answering who, what, when, where, why, and how
        - Clear attribution of information
        - Relevant context and background
        - Impact on stakeholders and broader community
        - Direct quotes or statements (when available)"""

        if not style:
            return base_prompt

        cefr_level = style.get('cefr_level', 'A1')
        tone = style.get('tone', 'neutral')

        cefr_guidelines = {
            'A1': """
            While maintaining hard news standards:
            - Use basic subject-verb-object sentence structure
            - Stick to present tense and simple past tense
            - Use high-frequency words and basic news vocabulary
            - Keep sentences very short and direct
            - Focus on concrete, observable facts""",
            
            'A2': """
            While maintaining hard news standards:
            - Use simple but varied sentence structures
            - Include basic time expressions and sequences
            - Expand vocabulary with common news terms
            - Connect ideas with basic conjunctions
            - Introduce simple supporting details""",
            
            'B1': """
            While maintaining hard news standards:
            - Use clear chronological sequences
            - Include cause and effect relationships
            - Expand news-specific vocabulary
            - Add relevant statistical information
            - Provide broader context with simple explanations""",
            
            'B2': """
            While maintaining hard news standards:
            - Include multiple perspectives and sources
            - Use more sophisticated news terminology
            - Add detailed background information
            - Explain complex relationships between events
            - Incorporate relevant data and analysis""",
            
            'C1': """
            While maintaining hard news standards:
            - Use full range of journalistic techniques
            - Include nuanced analysis and context
            - Handle complex political/economic concepts
            - Maintain sophisticated news register
            - Provide comprehensive background and implications"""
        }

        tone_guidelines = {
            'neutral': "Maintain strict journalistic objectivity, focusing solely on verifiable facts.",
            'optimistic': "While maintaining objectivity, include relevant positive developments and constructive responses.",
            'critical': "Maintain objectivity while thoroughly examining challenges and potential issues.",
            'balanced': "Present multiple perspectives with equal weight, supported by concrete evidence."
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
        Write a hard news article with the following specifications:

        KEY INFORMATION:
        Date: {time_period}
        Primary Topic: {node.attributes.topics[0]}
        Key Entity: {node.attributes.entities[0]}
        Main Event: {node.attributes.events[0]}
        Language Level: CEFR {cefr_level}

        STRUCTURAL REQUIREMENTS:
        1. Lead Paragraph:
           - Start with a strong news lead (first 35 words)
           - Answer who, what, when, where, why, and how
           - Emphasize the most newsworthy aspect

        2. Supporting Paragraphs:
           - Follow inverted pyramid structure
           - Include relevant context and background
           - Connect to broader implications
           - Maintain clear attribution

        3. Language Requirements:
           - Use appropriate CEFR {cefr_level} vocabulary and grammar
           - Maintain professional news register
           - Follow AP style guidelines
           - Keep total length around 100 words

        4. Focus Areas:
           - Emphasize factual reporting
           - Include relevant data or statistics
           - Connect local impact to broader significance
           - Maintain strict journalistic objectivity
        """

        # Add previous context if available
        if prev_node:
            prev_time = prev_node.time.strftime("%B %d, %Y")
            prompt += f"""
            PREVIOUS COVERAGE:
            Date: {prev_time}
            Related Entity: {prev_node.attributes.entities[0]}
            Previous Event: {prev_node.attributes.events[0]}
            
            Requirements for Continuity:
            - Reference relevant background from previous coverage
            - Show development of the ongoing story
            - Maintain clear chronological progression
            - Connect current events to previous developments
            """

        # Add CEFR-specific writing guidelines
        cefr_writing_tips = {
            'A1': """
            Writing Guidelines:
            - Use simple present and past tense
            - Focus on basic factual statements
            - Keep sentences very short (5-7 words)
            - Use only the most common news vocabulary
            - Avoid complex explanations""",
            
            'A2': """
            Writing Guidelines:
            - Use simple but clear sentence structures
            - Include basic time expressions
            - Keep sentences short (7-10 words)
            - Use common journalistic phrases
            - Add simple supporting details""",
            
            'B1': """
            Writing Guidelines:
            - Use clear chronological markers
            - Include cause and effect relationships
            - Write moderate length sentences (10-15 words)
            - Use standard news terminology
            - Add relevant context""",
            
            'B2': """
            Writing Guidelines:
            - Use varied sentence structures
            - Include multiple perspectives
            - Write varied length sentences (10-20 words)
            - Use professional news vocabulary
            - Add detailed background""",
            
            'C1': """
            Writing Guidelines:
            - Use sophisticated news writing techniques
            - Include nuanced analysis
            - Write natural length sentences
            - Use advanced journalistic vocabulary
            - Provide comprehensive context"""
        }

        prompt += f"""
        {cefr_writing_tips.get(cefr_level, cefr_writing_tips['A1'])}

        FINAL CHECKS:
        - Verify all facts are clearly stated
        - Ensure objective tone throughout
        - Maintain professional news style
        - Follow specified language level guidelines
        - Keep focus on hard news reporting
        """

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