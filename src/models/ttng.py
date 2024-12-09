from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple
from .narrative_context import NarrativeContext

@dataclass 
class Node:
    """Represents a node (fact) in the TTNG"""
    time: datetime
    attributes: NarrativeContext
    track_id: str

class TTNGModel:
    """Time-Track Narrative Graph Model Implementation"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Tuple[str, str]] = []
        self.tracks: Dict[str, List[str]] = {}
    
    def add_node(self, node_id: str, time: datetime, 
                context: NarrativeContext, track_id: str) -> None:
        """Add a node to the graph with its narrative context"""
        self.nodes[node_id] = Node(time, context, track_id)
        if track_id not in self.tracks:
            self.tracks[track_id] = []
        self.tracks[track_id].append(node_id)

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add an edge between nodes, enforcing temporal constraints"""
        if self.nodes[from_node].time >= self.nodes[to_node].time:
            raise ValueError("Edges must follow temporal order")
            
        # Check if nodes are in adjacent tracks
        from_track = self.nodes[from_node].track_id
        to_track = self.nodes[to_node].track_id
        if abs(int(from_track) - int(to_track)) > 1:
            raise ValueError("Can only connect adjacent tracks")
            
        self.edges.append((from_node, to_node))

    def validate_coherence(self, from_node: str, to_node: str) -> bool:
        """Validate that connected nodes share at least one NCE attribute"""
        n1 = self.nodes[from_node].attributes
        n2 = self.nodes[to_node].attributes
        
        # Check for shared entities, events or topics
        shared_entities = set(n1.entities) & set(n2.entities)
        shared_events = set(n1.events) & set(n2.events) 
        shared_topics = set(n1.topics) & set(n2.topics)
        
        return bool(shared_entities or shared_events or shared_topics) 