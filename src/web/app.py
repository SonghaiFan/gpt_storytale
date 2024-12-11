from flask import Flask, render_template, request, jsonify
from ..models.ttng import TTNGModel, OrganizingAttribute, GraphIdiom
from ..pipeline.graph_to_text import GraphToTextPipeline
import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    os.makedirs(log_dir, exist_ok=True)

    # Set up logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set up file handler for general logs
    general_log_path = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(
        general_log_path, maxBytes=1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Set up file handler for error logs
    error_log_path = os.path.join(log_dir, 'error.log')
    error_file_handler = RotatingFileHandler(
        error_log_path, maxBytes=1024*1024, backupCount=5
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)

def save_story(story_data: dict, context: dict, model: TTNGModel):
    """Save the generated story to a file with detailed attributes"""
    # Create stories directory if it doesn't exist
    stories_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../stories"))
    os.makedirs(stories_dir, exist_ok=True)

    # Create a timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    num_tracks = len(set(node['track'] for node in story_data['nodes']))
    num_timepoints = len(set(node['timepoint'] for node in story_data['nodes']))
    
    filename = f"story_{num_tracks}tracks_{num_timepoints}timepoints_{timestamp}.json"
    filepath = os.path.join(stories_dir, filename)

    # Collect node attributes
    nodes_with_attributes = []
    for node in story_data['nodes']:
        node_id = node['id']
        model_node = model.nodes[node_id]
        nodes_with_attributes.append({
            'id': node['id'],
            'text': node['text'],
            'track': node['track'],
            'timepoint': node['timepoint'],
            'attributes': {
                'topics': model_node.attributes.topics,
                'entities': model_node.attributes.entities,
                'events': model_node.attributes.events
            }
        })

    # Add metadata to the story
    story_with_metadata = {
        'metadata': {
            'generated_at': timestamp,
            'num_tracks': num_tracks,
            'num_timepoints': num_timepoints,
            'available_attributes': context  # Save all available attributes
        },
        'story': {
            'nodes': nodes_with_attributes,
            'edges': story_data['edges']
        }
    }

    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(story_with_metadata, f, indent=2, ensure_ascii=False)
    
    return filename, story_with_metadata

# Set up logging
logger = setup_logging()

# Create Flask app with explicit template and static folders
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)

@app.route('/')
def index():
    logger.info("Homepage accessed")
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        data = request.get_json()
        graph_data = data.get('graph', {})
        organizing_attribute = data.get('organizing_attribute', 'entity')
        style = data.get('style', {})
        
        if not graph_data or not graph_data.get('nodes'):
            return jsonify({'success': False, 'error': 'No graph data provided'})
        
        logger.info(f"Generating story for provided graph with {len(graph_data['nodes'])} nodes")
        logger.info(f"Using organizing attribute: {organizing_attribute}")
        
        # Initialize the model and pipeline
        try:
            # Convert string parameters to enums
            org_attr = OrganizingAttribute(organizing_attribute)
            idiom = GraphIdiom('thread')  # Fixed as thread for now
            
            model = TTNGModel(idiom=idiom, organizing_attribute=org_attr)
            pipeline = GraphToTextPipeline(model)
            
            # Initialize context
            context = pipeline.craft_narrative_context(org_attr)
            
            # Add custom attributes from graph nodes
            for node in graph_data['nodes']:
                if node.get('attributes'):
                    attrs = node['attributes']
                    if attrs.get('entities'):
                        context['entities'].extend(attrs['entities'])
                    if attrs.get('events'):
                        context['events'].extend(attrs['events'])
                    if attrs.get('topics'):
                        context['topics'].extend(attrs['topics'])
            
            # Remove duplicates and empty values
            context = {k: list(set(filter(None, v))) for k, v in context.items()}
            
            logger.info("Successfully initialized model and pipeline")
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f"Failed to initialize model: {str(e)}"})
        
        # Calculate time periods based on max timepoint
        max_timepoint = max(node['timepoint'] for node in graph_data['nodes'])
        time_periods = pipeline.calculate_time_periods(max_timepoint)
        
        story_data = {'nodes': [], 'edges': []}
        
        # Add nodes to model and generate text
        for node in graph_data['nodes']:
            try:
                node_id = node['id']
                logger.debug(f"Processing node {node_id}")
                
                # Create node context from attributes
                node_context = pipeline.map_attributes(
                    node_id,
                    context,
                    None,  # No previous node needed as we're using provided structure
                    node.get('attributes')  # Pass attributes directly
                )
                
                # Add node to model
                model.add_node(
                    node_id,
                    time_periods[node['timepoint'] - 1],
                    node_context,
                    str(node['track'])
                )
                
                # Generate text
                text = pipeline.generate_text(
                    model.nodes[node_id],
                    style=style
                )
                
                if not text:
                    raise ValueError(f"Generated text is empty for node {node_id}")
                
                story_data['nodes'].append({
                    'id': node_id,
                    'text': text,
                    'track': node['track'],
                    'timepoint': node['timepoint'],
                    'attributes': node_context.__dict__
                })
                
            except Exception as e:
                logger.error(f"Error processing node {node_id}: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f"Failed to process node {node_id}: {str(e)}"
                })
        
        # Add edges from input graph
        for edge in graph_data.get('edges', []):
            try:
                # Check if edge uses from/to or source/target format
                from_node = edge.get('from') or edge.get('source')
                to_node = edge.get('to') or edge.get('target')
                
                if not from_node or not to_node:
                    logger.warning(f"Invalid edge format: {edge}")
                    continue
                    
                model.add_edge(from_node, to_node)
                story_data['edges'].append({
                    'from': from_node,
                    'to': to_node
                })
                logger.debug(f"Added edge from {from_node} to {to_node}")
            except ValueError as e:
                logger.warning(f"Could not add edge: {str(e)}")
                # Continue even if edge can't be added due to constraints
        
        # Save the generated story
        try:
            filename, story_with_metadata = save_story(story_data, context, model)
            logger.info(f"Story saved to {filename}")
            story_data['saved_file'] = filename
        except Exception as e:
            logger.error(f"Error saving story: {str(e)}", exc_info=True)
            # Continue even if saving fails
        
        logger.info("Successfully generated complete story")
        return jsonify({'success': True, 'story': story_data})
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f"An unexpected error occurred: {str(e)}"})

def run_app():
    logger.info("Starting Flask application")
    app.run(debug=True)

if __name__ == '__main__':
    run_app() 