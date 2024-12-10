from typing import Optional
from ...models.ttng import Node
from .config import StyleConfig

class PromptManager:
    """Manages prompt generation and formatting"""
    
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
        
        cefr_guidelines = {
            'A1': "Use basic subject-verb-object structure...",
            'A2': "Use simple but varied sentence structures...",
            'B1': "Use clear chronological sequences...",
            'B2': "Include multiple perspectives and sources...",
            'C1': "Use full range of journalistic techniques..."
        }
        
        tone_guidelines = {
            'neutral': "Maintain strict journalistic objectivity...",
            'optimistic': "While maintaining objectivity, include relevant positive developments...",
            'critical': "Maintain objectivity while thoroughly examining challenges...",
            'balanced': "Present multiple perspectives with equal weight..."
        }
        
        return f"{base_prompt}\n{cefr_guidelines[style.cefr_level]}\n{tone_guidelines[style.tone]}"
    
    @staticmethod
    def create_narrative_prompt(node: Node, prev_node: Optional[Node], style: StyleConfig) -> str:
        """Create narrative prompt for text generation"""
        time_period = node.time.strftime("%B %d, %Y")
        
        prompt = f"""Write a hard news article with the following specifications:
        
        KEY INFORMATION:
        Date: {time_period}
        Primary Topic: {node.attributes.topics[0]}
        Key Entity: {node.attributes.entities[0]}
        Main Event: {node.attributes.events[0]}
        Language Level: CEFR {style.cefr_level}
        """
        
        # Add previous context if available
        if prev_node:
            prompt += PromptManager._add_previous_context(prev_node)
        
        # Add CEFR-specific guidelines
        prompt += PromptManager._get_cefr_guidelines(style.cefr_level)
        
        return prompt
    
    @staticmethod
    def _add_previous_context(prev_node: Node) -> str:
        """Add context from previous node to prompt"""
        return f"""
        PREVIOUS COVERAGE:
        Date: {prev_node.time.strftime("%B %d, %Y")}
        Related Entity: {prev_node.attributes.entities[0]}
        Previous Event: {prev_node.attributes.events[0]}
        """
    
    @staticmethod
    def _get_cefr_guidelines(cefr_level: str) -> str:
        """Get writing guidelines for CEFR level"""
        guidelines = {
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
        return guidelines[cefr_level] 