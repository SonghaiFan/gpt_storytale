import json
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models import TTNGModel
from src.pipeline import GraphToTextPipeline


def main():
    """Test narrative space generation"""
    try:
        # Load graph configuration
        config_path = Path(__file__).parent / "configs" / "demo_story.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Create and validate graph
        graph = TTNGModel.from_config(config)
        print("\nGraph validation successful!")
        
        # Initialize pipeline
        pipeline = GraphToTextPipeline(graph)
        
        # Generate narrative space
        narrative_space = pipeline.initialize_story_attributes()
        
        # Save narrative space
        output_path = Path(__file__).parent / "configs" / "narrative_space.json"
        with open(output_path, 'w') as f:
            json.dump(narrative_space, f, indent=4)
        
        print(f"\nNarrative space generated and saved to: {output_path}")
        print("\nNarrative Space Content:")
        print("======================")
        print(json.dumps(narrative_space, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 