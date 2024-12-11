import json
from pathlib import Path
from typing import Dict, List, Set
import openai
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models import TTNGModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up logging to file
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"openai_interactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def load_graph_config(file_path: Path) -> Dict:
    """Load graph configuration"""
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_narrative_space(structure: Dict) -> Dict:
    """Generate narrative space using OpenAI API"""
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

    messages = [
        {"role": "system", "content": "You are a narrative designer creating story elements."},
        {"role": "user", "content": prompt}
    ]
    
    # Log the prompt
    logger.info("Sending prompt to OpenAI:")
    logger.info("System message: %s", messages[0]['content'])
    logger.info("User message: %s", messages[1]['content'])
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    # Log the response
    response_content = response.choices[0].message.content
    logger.info("Received response from OpenAI:")
    logger.info(response_content)
    
    return json.loads(response_content)

def main():
    # Load graph configuration
    config_path = Path(__file__).parent / "configs" / "demo_story.json"
    config = load_graph_config(config_path)
    
    try:
        # Create and validate graph
        graph = TTNGModel.from_config(config)
        print("\nGraph validation successful!")
        
        # Get graph dimensions
        structure = graph.get_graph_dimensions()
        print("\nGraph Structure:")
        print("===============")
        print(f"Timepoints: {structure['timepoints']}")
        print(f"Tracks: {structure['tracks']}")
        print(f"Total Nodes: {structure['total_nodes']}")
        
        # Generate narrative space
        narrative_space = generate_narrative_space(structure)
        
        # Save narrative space
        output_path = Path(__file__).parent / "configs" / "narrative_space.json"
        with open(output_path, 'w') as f:
            json.dump(narrative_space, f, indent=4)
        
        print(f"\nNarrative space generated and saved to: {output_path}")
        
    except ValueError as e:
        print(f"\nError: Graph validation failed!")
        print(f"Reason: {str(e)}")

if __name__ == "__main__":
    main() 