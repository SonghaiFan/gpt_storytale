import json
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models import TTNGModel
from src.pipeline import GraphToTextPipeline
from src.pipeline.components.logger_config import setup_logger

# Get logger for this module
logger = setup_logger(__name__)

def main():
    """Test story generation pipeline"""
    try:
        # Load configurations
        configs_dir = Path(__file__).parent / "configs"
        
        # Load graph structure
        with open(configs_dir / "demo_story.json", 'r') as f:
            graph_config = json.load(f)
            
        # Create graph model
        graph = TTNGModel.from_config(graph_config)
        logger.info("Graph validation successful!")
        
        # Initialize pipeline
        pipeline = GraphToTextPipeline(graph)
        
        # Generate narrative attributes for all nodes
        pipeline.generate_node_attributes()
        logger.info("Generated narrative attributes for all nodes")
        
        # Generate story for each node
        story_segments = []
        sorted_nodes = sorted(graph.nodes.items(), key=lambda x: x[1].time)
        
        for node_id, node in sorted_nodes:
            logger.info(f"Generating text for node {node_id}")
            # Generate text with style preferences
            style = {
                'cefr_level': 'B2',
                'tone': 'balanced'
            }
            text = pipeline.generate_text(node, style)
            
            # Store segment information
            story_segments.append({
                'node_id': node_id,
                'time': node.time.isoformat(),
                'track': node.track_id,
                'text': text
            })
        
        # Save complete story with all context
        output = {
            'graph_config': graph_config,
            'story_segments': story_segments
        }
        
        output_path = configs_dir / "generated_story.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=4)
        
        logger.info(f"Complete story saved to: {output_path}")
        
        # Print story segments
        print("\nGenerated Story:")
        print("================")
        for segment in story_segments:
            print(f"\nNode {segment['node_id']} (Track {segment['track']}, Time: {segment['time']}):")
            print(segment['text'])
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 