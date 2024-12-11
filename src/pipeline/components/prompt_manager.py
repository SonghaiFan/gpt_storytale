"""
Prompt management for the story generation pipeline.
"""

from typing import Dict, List, Optional
from src.models.ttng import Node
from .config import StyleConfig

class PromptManager:
    """Manages prompt generation and templates in the pipeline"""
    
    @staticmethod
    def create_system_prompt(style: StyleConfig) -> str:
        """Create system prompt based on style configuration"""
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
        
        tone_guidelines = {
            'neutral': "Maintain strict journalistic objectivity and balanced reporting.",
            'optimistic': "While maintaining objectivity, highlight constructive developments and potential solutions.",
            'critical': "Maintain objectivity while thoroughly examining challenges and implications.",
            'balanced': "Present multiple perspectives with equal weight and thorough analysis."
        }
        
        # Add CEFR-specific guidelines
        cefr_guidelines = PromptManager._get_cefr_guidelines(style.cefr_level)
        
        return f"{base_prompt}\n\n{tone_guidelines[style.tone]}\n\n{cefr_guidelines}"
    
    @staticmethod
    def create_narrative_space_prompt(structure: Dict[str, int]) -> List[Dict[str, str]]:
        """Create prompt for narrative space generation"""
        prompt = f"""Given a story structure with:
- {structure['timepoints']} timepoints
- {structure['tracks']} parallel tracks
- {structure['total_nodes']} total story nodes

Generate a narrative space with entities, events, and topics that could form a narrative news focuses on timely and consequential events or incidents that impact people locally, regionally, nationally, or internationally. The content should reflect journalistic style and genre, covering topics such as politics, international affairs, economics, and science.

The response should be a JSON object with three lists:
1. entities: a list of key individuals, organizations, or institutions involved in the news
2. events: a list of significant and timely incidents or actions
3. topics: a list of themes or subjects relevant to news

Each track should maintain coherence through shared entities, while events and topics can vary.
Format the response as a valid JSON object."""

        return [
            {"role": "system", "content": "You are a narrative designer creating story elements."},
            {"role": "user", "content": prompt}
        ]
    
    @staticmethod
    def create_narrative_prompt(node: Node, prev_node: Optional[Node], style: StyleConfig) -> str:
        """Create narrative prompt for text generation"""
        time_period = node.time.strftime("%B %d, %Y %H:%M")
        
        # Get attributes from node
        entities = node.attributes.entities if node.attributes else []
        events = node.attributes.events if node.attributes else []
        topics = node.attributes.topics if node.attributes else []
        
        prompt = f"""Write a news article based on the following attributes:

KEY INFORMATION:
Time: {time_period}
Key Entities: {', '.join(entities)}
Current Events: {', '.join(events)}
Topics: {', '.join(topics)}
Style: {style.tone}
Language Level: CEFR {style.cefr_level}
"""
        
        # Add previous context if available
        if prev_node and prev_node.attributes:
            prev_time = prev_node.time.strftime("%B %d, %Y %H:%M")
            prev_entities = prev_node.attributes.entities
            prev_events = prev_node.attributes.events
            prompt += f"""
PREVIOUS CONTEXT:
Time: {prev_time}
Related Entities: {', '.join(prev_entities)}
Previous Events: {', '.join(prev_events)}
"""
        
        # Add writing guidelines
        prompt += """
WRITING GUIDELINES:
- Focus on factual reporting
- Use clear and concise language
- Include relevant context and background
- Maintain journalistic objectivity
- Connect to broader implications
"""
        
        # Add CEFR-specific guidelines
        prompt += PromptManager._get_cefr_guidelines(style.cefr_level)
        
        return prompt
    
    @staticmethod
    def _get_cefr_guidelines(cefr_level: str) -> str:
        """Get language guidelines based on CEFR level"""
        guidelines = {
            'A1': """
LANGUAGE GUIDELINES:
- Use very simple present tense sentences
- Focus on concrete, everyday topics
- Use basic, high-frequency vocabulary
- Keep sentences short and direct
""",
            'A2': """
LANGUAGE GUIDELINES:
- Use simple present and past tense
- Connect ideas with basic conjunctions
- Use common vocabulary and phrases
- Keep paragraphs short and focused
""",
            'B1': """
LANGUAGE GUIDELINES:
- Use a mix of simple and compound sentences
- Include some idiomatic expressions
- Maintain clear chronological order
- Express opinions with simple justifications
""",
            'B2': """
LANGUAGE GUIDELINES:
- Use varied sentence structures
- Include topic-specific vocabulary
- Express clear cause and effect
- Provide detailed descriptions
- Use appropriate register
""",
            'C1': """
LANGUAGE GUIDELINES:
- Use complex sentence structures
- Include sophisticated vocabulary
- Express nuanced viewpoints
- Use advanced cohesive devices
- Maintain formal academic style
"""
        }
        return guidelines[cefr_level] 