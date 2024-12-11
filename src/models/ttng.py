from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional
from .narrative_context import NarrativeContext
from enum import Enum

class OrganizingAttribute(Enum):
    ENTITY = "entity"
    EVENT = "event"
    TOPIC = "topic"

class GraphIdiom(Enum):
    THREAD = "thread"  # deg(vi) ≤ 2
    TREE = "tree"     # degin(vi) ≤ 1
    MAP = "map"       # unrestricted

@dataclass 
class Node:
    """Represents a node (fact) in the TTNG"""
    time: datetime
    track_id: str
    attributes: Optional[NarrativeContext] = None

class TTNGModel:
    """Time-Track Narrative Graph Model Implementation"""
    
    def __init__(self, idiom: GraphIdiom = GraphIdiom.THREAD, 
                 organizing_attribute: OrganizingAttribute = OrganizingAttribute.ENTITY):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Tuple[str, str]] = []
        self.tracks: Dict[str, List[str]] = {}
        self.idiom = idiom
        self.organizing_attribute = organizing_attribute
    
    def add_node(self, node_id: str, time: datetime, 
                context: Optional[NarrativeContext], track_id: str) -> None:
        """Add a node to the graph, attributes can be added later"""
        self.nodes[node_id] = Node(time, track_id, context)
        if track_id not in self.tracks:
            self.tracks[track_id] = []
        self.tracks[track_id].append(node_id)

    def validate_idiom_constraints(self, from_node: str, to_node: str) -> bool:
        """Validate idiom-specific constraints"""
        if self.idiom == GraphIdiom.THREAD:
            # Check if adding this edge would exceed degree 2
            from_degree = sum(1 for edge in self.edges if from_node in edge)
            to_degree = sum(1 for edge in self.edges if to_node in edge)
            return from_degree < 2 and to_degree < 2
        
        elif self.idiom == GraphIdiom.TREE:
            # Check if target node already has an incoming edge
            to_in_degree = sum(1 for _, target in self.edges if target == to_node)
            return to_in_degree == 0
        
        return True  # MAP idiom has no restrictions

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add an edge between nodes, enforcing temporal and idiom constraints"""
        # Temporal constraint
        if self.nodes[from_node].time >= self.nodes[to_node].time:
            raise ValueError("Edges must follow temporal order")
            
        # Adjacent track constraint
        from_track = self.nodes[from_node].track_id
        to_track = self.nodes[to_node].track_id
        if abs(int(from_track) - int(to_track)) > 1:
            raise ValueError("Can only connect adjacent tracks")
        
        # Idiom constraint
        if not self.validate_idiom_constraints(from_node, to_node):
            raise ValueError(f"Edge violates {self.idiom.value} idiom constraints")
            
        # Coherence constraint - only check if both nodes have attributes
        if (self.nodes[from_node].attributes is not None and 
            self.nodes[to_node].attributes is not None and
            not self.validate_coherence(from_node, to_node)):
            raise ValueError("Connected nodes must share at least one NCE attribute")
            
        self.edges.append((from_node, to_node))

    def validate_coherence(self, from_node: str, to_node: str) -> bool:
        """Validate that connected nodes share at least one NCE attribute at the selected level"""
        n1 = self.nodes[from_node].attributes
        n2 = self.nodes[to_node].attributes
        
        # If either node lacks attributes, skip coherence check
        if n1 is None or n2 is None:
            return True
            
        # Check based on organizing attribute
        if self.organizing_attribute == OrganizingAttribute.ENTITY:
            return bool(set(n1.entities) & set(n2.entities))
        elif self.organizing_attribute == OrganizingAttribute.EVENT:
            return bool(set(n1.events) & set(n2.events))
        elif self.organizing_attribute == OrganizingAttribute.TOPIC:
            return bool(set(n1.topics) & set(n2.topics))
        
        # Fallback to checking all attributes
        shared_entities = set(n1.entities) & set(n2.entities)
        shared_events = set(n1.events) & set(n2.events) 
        shared_topics = set(n1.topics) & set(n2.topics)
        
        return bool(shared_entities or shared_events or shared_topics)

    def get_track_attributes(self, track_id: str) -> Set[str]:
        """Get all attributes for a track based on organizing attribute"""
        attributes = set()
        for node_id in self.tracks.get(track_id, []):
            node = self.nodes[node_id]
            if node.attributes is None:
                continue
            if self.organizing_attribute == OrganizingAttribute.ENTITY:
                attributes.update(node.attributes.entities)
            elif self.organizing_attribute == OrganizingAttribute.EVENT:
                attributes.update(node.attributes.events)
            else:
                attributes.update(node.attributes.topics)
        return attributes

    def get_node_degree(self, node_id: str) -> tuple[int, int]:
        """Get in-degree and out-degree of a node"""
        in_degree = sum(1 for _, target in self.edges if target == node_id)
        out_degree = sum(1 for source, _ in self.edges if source == node_id)
        return (in_degree, out_degree)

    def get_track_connections(self, track_id: str) -> List[str]:
        """Get all tracks connected to given track"""
        connected_tracks = set()
        for from_node, to_node in self.edges:
            if self.nodes[from_node].track_id == track_id:
                connected_tracks.add(self.nodes[to_node].track_id)
            if self.nodes[to_node].track_id == track_id:
                connected_tracks.add(self.nodes[from_node].track_id)
        return list(connected_tracks)

    @classmethod
    def from_config(cls, config: Dict) -> 'TTNGModel':
        """Create TTNGModel from configuration dictionary"""
        # Initialize model with settings
        model = cls(
            idiom=GraphIdiom[config['graph_settings']['idiom']],
            organizing_attribute=OrganizingAttribute[config['graph_settings']['organizing_attribute']]
        )
        
        # Add nodes
        for node_data in config['nodes']:
            track_id = str(node_data['y'])
            model.add_node(
                node_id=node_data['id'],
                time=datetime.fromtimestamp(node_data['x']),  # Using x as timestamp for now
                context=None,  # Will be populated later
                track_id=track_id
            )
        
        # Add edges
        for edge in config['edges']:
            model.add_edge(edge['from'], edge['to'])
        
        # Validate the entire graph
        model.validate_graph()
        
        return model

    def validate_graph(self) -> None:
        """Validate the entire graph structure"""
        self._validate_node_degrees()
        self._validate_temporal_order()
        self._validate_track_connections()

    def _validate_node_degrees(self) -> None:
        """Validate node degrees based on idiom"""
        for node_id in self.nodes:
            in_degree, out_degree = self.get_node_degree(node_id)
            total_degree = in_degree + out_degree
            
            if self.idiom == GraphIdiom.THREAD and total_degree > 2:
                raise ValueError(
                    f"Node {node_id} has degree {total_degree}, "
                    f"exceeding THREAD idiom constraint (max degree 2)"
                )
            elif self.idiom == GraphIdiom.TREE and in_degree > 1:
                raise ValueError(
                    f"Node {node_id} has in-degree {in_degree}, "
                    f"exceeding TREE idiom constraint (max in-degree 1)"
                )

    def _validate_temporal_order(self) -> None:
        """Validate temporal ordering of edges"""
        for from_node, to_node in self.edges:
            if self.nodes[from_node].time >= self.nodes[to_node].time:
                raise ValueError(
                    f"Edge {from_node}->{to_node} violates temporal order: "
                    f"{self.nodes[from_node].time} >= {self.nodes[to_node].time}"
                )

    def _validate_track_connections(self) -> None:
        """Validate connections between tracks"""
        for from_node, to_node in self.edges:
            from_track = int(self.nodes[from_node].track_id)
            to_track = int(self.nodes[to_node].track_id)
            
            if abs(from_track - to_track) > 1:
                raise ValueError(
                    f"Edge {from_node}->{to_node} connects non-adjacent tracks: "
                    f"{from_track} -> {to_track}"
                )

    def get_graph_dimensions(self) -> Dict[str, int]:
        """Get the dimensions of the graph"""
        if not self.nodes:
            return {'timepoints': 0, 'tracks': 0, 'total_nodes': 0}
            
        # Get max x and y coordinates
        max_x = max(1 for node in self.nodes.values())  # Using time for x
        max_y = max(int(node.track_id) for node in self.nodes.values())
        
        return {
            'timepoints': max_x,
            'tracks': max_y,
            'total_nodes': len(self.nodes)
        }