from typing import Dict, Optional
import networkx as nx
import matplotlib.pyplot as plt
import json
from pathlib import Path
from ...models.ttng import TTNGModel

class GraphVisualizer:
    """Handles graph visualization and export"""
    
    @staticmethod
    def visualize(model: TTNGModel, output_path: Optional[str] = None, show: bool = True) -> None:
        """Visualize the story graph structure"""
        G = nx.DiGraph()
        
        # Add nodes and edges
        GraphVisualizer._add_nodes_and_edges(G, model)
        
        # Create visualization
        plt.figure(figsize=(15, 10))
        pos = GraphVisualizer._calculate_node_positions(G)
        
        GraphVisualizer._draw_graph(G, pos)
        
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
        
        if show:
            plt.show()
        else:
            plt.close()
    
    @staticmethod
    def export_json(model: TTNGModel, output_path: str) -> None:
        """Export graph data as JSON"""
        graph_data = {
            'nodes': [
                {
                    'id': node_id,
                    'track': node.track_id,
                    'time': node.time.isoformat(),
                    'attributes': node.attributes.__dict__
                }
                for node_id, node in model.nodes.items()
            ],
            'edges': [{'source': edge[0], 'target': edge[1]} for edge in model.edges]
        }
        
        Path(output_path).write_text(json.dumps(graph_data, indent=2))
    
    @staticmethod
    def _add_nodes_and_edges(G: nx.DiGraph, model: TTNGModel) -> None:
        """Add nodes and edges to the graph"""
        for node_id, node in model.nodes.items():
            label = (f"Track {node.track_id}\n{node.time.strftime('%Y-%m-%d')}\n"
                    f"Topic: {node.attributes.topics[0]}\n"
                    f"Entity: {node.attributes.entities[0]}")
            G.add_node(node_id, label=label, track=int(node.track_id), time=node.time)
        
        for edge in model.edges:
            G.add_edge(edge[0], edge[1])
    
    @staticmethod
    def _calculate_node_positions(G: nx.DiGraph) -> Dict:
        """Calculate node positions for visualization"""
        pos = {}
        track_nodes = {}
        
        for node in G.nodes():
            track = G.nodes[node]['track']
            track_nodes.setdefault(track, []).append(node)
        
        for track, nodes in track_nodes.items():
            nodes.sort(key=lambda x: G.nodes[x]['time'])
            y = (track - 1) * 2
            for i, node in enumerate(nodes):
                pos[node] = (i * 3, y)
        
        return pos
    
    @staticmethod
    def _draw_graph(G: nx.DiGraph, pos: Dict) -> None:
        """Draw the graph with specified layout"""
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000, alpha=0.7)
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)
        
        labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels, font_size=8, font_family='sans-serif')
        
        plt.title("Story Graph Structure", pad=20, size=16)
        plt.axis('off') 