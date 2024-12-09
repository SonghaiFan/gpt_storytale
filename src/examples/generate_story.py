from datetime import datetime, timedelta
from ..models.ttng import TTNGModel
from ..models.narrative_context import NarrativeContext
from ..pipeline.graph_to_text import GraphToTextPipeline

def generate_example_story():
    # Initialize the model and pipeline
    model = TTNGModel()
    pipeline = GraphToTextPipeline(model)
    
    # Get narrative context
    context = pipeline.craft_narrative_context()
    
    # Create a simple story with 3 tracks and 2 time points
    base_time = datetime.now()
    
    # Add nodes for first time point
    for track in ['1', '2', '3']:
        node_id = f"t1_track{track}"
        node_context = pipeline.map_attributes(node_id, context)
        model.add_node(node_id, base_time, node_context, track)
    
    # Add nodes for second time point
    for track in ['1', '2', '3']:
        node_id = f"t2_track{track}"
        node_context = pipeline.map_attributes(node_id, context)
        model.add_node(node_id, base_time + timedelta(days=1), node_context, track)
    
    # Add edges between nodes
    model.add_edge("t1_track1", "t2_track1")
    model.add_edge("t1_track2", "t2_track2")
    model.add_edge("t1_track3", "t2_track3")
    
    # Generate text for each node
    for node_id in model.nodes:
        text = pipeline.generate_text(model.nodes[node_id])
        print(f"\nNode {node_id}:")
        print(text)

if __name__ == "__main__":
    generate_example_story() 