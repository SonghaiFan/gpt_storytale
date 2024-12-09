from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set
from .narrative_context import NarrativeContext
from enum import Enum

class OrganizingAttribute(Enum):
    ENTITY = "entity"
    EVENT = "event"
    TOPIC = "topic"

class GraphGenre(Enum):
    THREAD = "thread"  # deg(vi) ≤ 2
    TREE = "tree"     # degin(vi) ≤ 1
    MAP = "map"       # unrestricted

@dataclass 
class Node:
    """Represents a node (fact) in the TTNG"""
    time: datetime
    attributes: NarrativeContext
    track_id: str

class TTNGModel:
    """Time-Track Narrative Graph Model Implementation"""
    
    def __init__(self, genre: GraphGenre = GraphGenre.THREAD, 
                 organizing_attribute: OrganizingAttribute = OrganizingAttribute.ENTITY):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Tuple[str, str]] = []
        self.tracks: Dict[str, List[str]] = {}
        self.genre = genre
        self.organizing_attribute = organizing_attribute
    
    def add_node(self, node_id: str, time: datetime, 
                context: NarrativeContext, track_id: str) -> None:
        """Add a node to the graph with its narrative context"""
        self.nodes[node_id] = Node(time, context, track_id)
        if track_id not in self.tracks:
            self.tracks[track_id] = []
        self.tracks[track_id].append(node_id)

    def validate_genre_constraints(self, from_node: str, to_node: str) -> bool:
        """Validate genre-specific constraints"""
        if self.genre == GraphGenre.THREAD:
            # Check if adding this edge would exceed degree 2
            from_degree = sum(1 for edge in self.edges if from_node in edge)
            to_degree = sum(1 for edge in self.edges if to_node in edge)
            return from_degree < 2 and to_degree < 2
        
        elif self.genre == GraphGenre.TREE:
            # Check if target node already has an incoming edge
            to_in_degree = sum(1 for _, target in self.edges if target == to_node)
            return to_in_degree == 0
        
        return True  # MAP genre has no restrictions

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add an edge between nodes, enforcing temporal and genre constraints"""
        # Temporal constraint
        if self.nodes[from_node].time >= self.nodes[to_node].time:
            raise ValueError("Edges must follow temporal order")
            
        # Adjacent track constraint
        from_track = self.nodes[from_node].track_id
        to_track = self.nodes[to_node].track_id
        if abs(int(from_track) - int(to_track)) > 1:
            raise ValueError("Can only connect adjacent tracks")
        
        # Genre constraint
        if not self.validate_genre_constraints(from_node, to_node):
            raise ValueError(f"Edge violates {self.genre.value} genre constraints")
            
        # Coherence constraint
        if not self.validate_coherence(from_node, to_node):
            raise ValueError("Connected nodes must share at least one NCE attribute")
            
        self.edges.append((from_node, to_node))

    def validate_coherence(self, from_node: str, to_node: str) -> bool:
        """Validate that connected nodes share at least one NCE attribute at the selected level"""
        n1 = self.nodes[from_node].attributes
        n2 = self.nodes[to_node].attributes
        
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
            if self.organizing_attribute == OrganizingAttribute.ENTITY:
                attributes.update(node.attributes.entities)
            elif self.organizing_attribute == OrganizingAttribute.EVENT:
                attributes.update(node.attributes.events)
            else:
                attributes.update(node.attributes.topics)
        return attributes