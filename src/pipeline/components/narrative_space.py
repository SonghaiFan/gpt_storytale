"""
Narrative space management for the story generation pipeline.
"""

import json
import logging
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class NarrativeSpaceManager:
    """Manages narrative space generation and management in the pipeline"""
    
    def __init__(self, narrative_space_path: Path = None):
        # Initialize OpenAI client
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.prompt_manager = PromptManager()
        self.narrative_space_path = narrative_space_path
        self._narrative_space = None
    
    def get_context(self, narrative_space_path: Path = None) -> Dict[str, List[str]]:
        """
        Get narrative context from specified path or cached data
        
        Args:
            narrative_space_path: Path to narrative space JSON file. If None, uses path from initialization
            
        Returns:
            Dict containing narrative space elements
        """
        try:
            # Return cached narrative space if available
            if self._narrative_space is not None:
                return self._narrative_space
            
            # Use provided path or fall back to initialized path
            path_to_use = narrative_space_path or self.narrative_space_path
            if not path_to_use:
                raise ValueError("No narrative space path provided")
            
            if path_to_use.exists():
                with open(path_to_use, 'r') as f:
                    self._narrative_space = json.load(f)
                logger.info("Loaded narrative space from: %s", path_to_use)
                return self._narrative_space
            
            logger.warning("No narrative space found at: %s", path_to_use)
            return {}
            
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return {}
    
    def _generate_narrative_space(self, structure: Dict[str, int]) -> Dict[str, List[str]]:
        """Generate narrative space using OpenAI API"""
        messages = self.prompt_manager.create_narrative_space_prompt(structure)
        
        # Log the prompt
        logger.info("\n=== Generating Narrative Space ===")
        logger.info("Structure: %s", structure)
        logger.info("System message: %s", messages[0]['content'])
        logger.info("User message: %s", messages[1]['content'])
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        # Log the response
        response_content = response.choices[0].message.content
        logger.info("Received narrative space from OpenAI:")
        logger.info(response_content)
        logger.info("=== Narrative Space Generation Complete ===\n")
        
        # Cache the generated narrative space
        self._narrative_space = json.loads(response_content)
        return self._narrative_space
    
    def initialize_story_attributes(self, structure: Dict[str, int]) -> Dict[str, List[str]]:
        """Initialize story attributes by generating narrative space"""
        return self._generate_narrative_space(structure) 