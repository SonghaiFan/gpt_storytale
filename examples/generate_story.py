from datetime import datetime
from typing import Dict, List
import json
import os
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models import TTNGModel, GraphIdiom, OrganizingAttribute, NarrativeContext
from src.pipeline import GraphToTextPipeline

def load_config(file_path: Path) -> Dict:
    """Load configuration from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def create_ttng_graph(graph_config: Dict, narrative_space: Dict) -> TTNGModel:
    """Create TTNG graph from configuration and narrative space"""
    # Initialize TTNG with configured idiom and organizing attribute
    graph = TTNGModel(
        idiom=GraphIdiom[graph_config['graph_settings']['idiom']],
        organizing_attribute=OrganizingAttribute[graph_config['graph_settings']['organizing_attribute']]
    )
    
    # Add nodes
    for node_data in graph_config['nodes']:
        time = datetime.fromtimestamp(node_data['x'])
        track_id = str(node_data['y'])
        
        # Create initial narrative context based on track
        # Each track will share some entities for coherence
        track_idx = int(track_id) - 1  # 0-based index for array access
        context = NarrativeContext(
            entities=[narrative_space['entities'][track_idx]],  # Each track gets its primary entity
            events=[narrative_space['events'][track_idx]],      # And its primary event
            topics=[narrative_space['topics'][track_idx]]       # And its primary topic
        )
        
        graph.add_node(
            node_id=node_data['id'],
            time=time,
            context=context,
            track_id=track_id
        )
    
    # Add edges
    for edge in graph_config['edges']:
        try:
            graph.add_edge(edge['from'], edge['to'])
        except ValueError as e:
            print(f"Warning: Skipping edge {edge['from']}->{edge['to']}: {str(e)}")
    
    return graph

def generate_narrative(graph: TTNGModel, narrative_space: Dict) -> List[str]:
    """Generate narrative text for each node in the graph"""
    pipeline = GraphToTextPipeline(graph)
    narrative_segments = []
    
    # Process nodes in temporal order
    sorted_nodes = sorted(graph.nodes.items(), key=lambda x: x[1].time)
    
    for node_id, node in sorted_nodes:
        style = {
            'cefr_level': 'B2',
            'tone': 'balanced'
        }
        text = pipeline.generate_text(node, style)
        narrative_segments.append({
            'node_id': node_id,
            'time': node.time.isoformat(),
            'track': node.track_id,
            'text': text
        })
    
    return narrative_segments

def main():
    examples_dir = Path(__file__).parent
    configs_dir = examples_dir / "configs"
    
    # Load configurations
    graph_config = load_config(configs_dir / "demo_story.json")
    narrative_space = load_config(configs_dir / "narrative_space.json")
    
    # Create TTNG graph with narrative attributes
    graph = create_ttng_graph(graph_config, narrative_space)
    
    # Generate narrative
    narrative = generate_narrative(graph, narrative_space)
    
    # Print the generated story
    print("\nGenerated Story:")
    print("================")
    for segment in narrative:
        print(f"\nNode {segment['node_id']} (Track {segment['track']}, Time: {segment['time']}):")
        print(segment['text'])
    
    # Save the complete story
    output = {
        'graph_config': graph_config,
        'narrative_space': narrative_space,
        'story_segments': narrative
    }
    
    output_path = configs_dir / "generated_story.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=4)
    
    print(f"\nComplete story saved to: {output_path}")

if __name__ == "__main__":
    main() 