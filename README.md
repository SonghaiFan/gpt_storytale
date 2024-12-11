# GPT Storytale

Create controllable story sequences with transformers that can be used in user-evaluation studies of text-to-visualisation pipelines.

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/[username]/gpt-storytale.git
cd gpt-storytale
```

2. Set up a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up your OpenAI API key:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## Using the Web Interface

1. Start the web server:

```bash
python -m src.web.run
```

2. Open your browser and navigate to `http://localhost:5000`

3. Use the interface to:
   - Select the number of story tracks (1-5)
   - Choose the number of timepoints (2-5)
   - Generate coherent story sequences
   - View the generated stories in an interactive grid

## Monitoring and Logs

The application maintains detailed logs in the `logs` directory:

- `logs/app.log`: General application logs (INFO level and above)

  - Story generation attempts
  - Model initialization
  - Application flow

- `logs/error.log`: Error-specific logs
  - API errors
  - Text generation failures
  - System errors

Monitor logs in real-time:

```bash
tail -f logs/app.log    # For general logs
tail -f logs/error.log  # For error logs
```

## Using Your Own Story Configuration

1. Create a JSON file following the format in `examples/simple_story.json`
2. Run the generator with your config:

```bash
python -m src.examples.generate_story --config path/to/your/config.json
```

## Project Structure

```
gpt_storytale/
├── src/
│   ├── web/              # Web interface
│   │   ├── templates/    # HTML templates
│   │   ├── static/       # CSS and JavaScript
│   │   └── app.py       # Flask application
│   ├── models/          # Core models
│   ├── pipeline/        # Text generation pipeline
│   └── examples/        # Example scripts
├── logs/               # Application logs
├── stories/           # Generated stories
└── examples/          # Example configurations
```

## Features

- Web-based story generation interface
- Multi-track narrative generation
- Temporal coherence across story points
- OpenAI GPT integration
- Detailed logging system
- Configurable story parameters
- Interactive story visualization

## Dependencies

- Flask >= 2.0.0
- OpenAI >= 1.0.0
- Python-dotenv
- Langchain
- Pytest >= 7.0.0

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## TTNG Model Documentation

### Overview

The Time-Track Narrative Graph (TTNG) model is a specialized graph structure designed for narrative organization and generation. It combines temporal ordering with parallel tracks to represent and manage complex narrative structures.

### Core Classes

#### `TTNGModel`

Main class implementing the Time-Track Narrative Graph.

```python
TTNGModel(
    idiom: GraphIdiom = GraphIdiom.THREAD,
    organizing_attribute: OrganizingAttribute = OrganizingAttribute.ENTITY,
    start_date: datetime = datetime.now(),
    time_step_days: int = 7
)
```

Parameters:

- `idiom`: Graph structure type (THREAD, TREE, or MAP)
- `organizing_attribute`: Primary organization method (ENTITY, EVENT, or TOPIC)
- `start_date`: Starting date for temporal calculations
- `time_step_days`: Time step size in days

#### `NarrativeSpace`

Container for narrative context elements.

```python
NarrativeSpace(
    entities: List[str] = None,  # Characters, objects, locations
    events: List[str] = None,    # Actions, happenings
    topics: List[str] = None     # Themes, subjects
)
```

#### `Node`

Represents a single node in the graph.

```python
Node(
    time: datetime,
    track_id: str,
    time_index: int,
    attributes: Optional[NarrativeSpace] = None
)
```

### Graph Idioms

1. **THREAD**

   - Each node has maximum degree ≤ 2
   - Best for linear narratives with occasional branches

2. **TREE**

   - Each node has maximum in-degree ≤ 1
   - Suitable for hierarchical narratives

3. **MAP**
   - No degree restrictions
   - Allows complex narrative networks

### Organizing Attributes

1. **ENTITY**

   - Organizes narrative around characters/objects
   - Ensures coherence through shared entities

2. **EVENT**

   - Organizes narrative around actions/happenings
   - Maintains coherence through related events

3. **TOPIC**
   - Organizes narrative around themes
   - Ensures thematic coherence

### Key Methods

#### Node Management

```python
add_node(
    node_id: str,
    time_index: int,
    track_id: str,
    context: Optional[NarrativeSpace] = None
)
```

#### Edge Management

```python
add_edge(from_node: str, to_node: str)
```

#### Validation Methods

```python
validate_graph()
validate_idiom_constraints(from_node: str, to_node: str) -> bool
validate_coherence(from_node: str, to_node: str) -> bool
```

#### Track Operations

```python
get_track_attributes(track_id: str) -> Set[str]
get_track_connections(track_id: str) -> List[str]
```

#### Graph Analysis

```python
get_node_degree(node_id: str) -> tuple[int, int]
get_graph_dimensions() -> Dict[str, int]
```

### Constraints

1. **Temporal Constraints**

   - Edges must follow temporal order
   - Node times are calculated based on time_index and step size

2. **Track Constraints**

   - Only adjacent tracks can be connected
   - Track IDs must be sequential

3. **Coherence Constraints**
   - Connected nodes must share at least one NCE attribute
   - Coherence checking based on organizing_attribute

### Configuration

Creating from Config:

```python
@classmethod
def from_config(cls, config: Dict) -> 'TTNGModel'
```

Example config structure:

```python
{
    "graph_settings": {
        "idiom": "THREAD",
        "organizing_attribute": "ENTITY",
        "time_settings": {
            "start_date": "2024-01-01",
            "time_step_days": 7
        }
    },
    "nodes": [...],
    "edges": [...]
}
```

### Usage Example

```python
# Create a new TTNG model
model = TTNGModel(
    idiom=GraphIdiom.THREAD,
    organizing_attribute=OrganizingAttribute.ENTITY
)

# Add nodes with narrative context
context = NarrativeSpace(
    entities=["Alice"],
    events=["Meeting"],
    topics=["Friendship"]
)
model.add_node("node1", time_index=1, track_id="1", context=context)

# Add edges
model.add_edge("node1", "node2")

# Validate the graph
model.validate_graph()
```

### Error Handling

The model raises `ValueError` for:

- Invalid temporal ordering
- Idiom constraint violations
- Track connection violations
- Coherence violations

### Best Practices

1. Always validate the graph after construction
2. Maintain consistent narrative contexts
3. Choose appropriate idiom for narrative structure
4. Consider temporal spacing carefully
5. Use meaningful track organization

This model is particularly useful for:

- Story generation
- Narrative planning
- Content organization
- Interactive storytelling
- Parallel narrative management
