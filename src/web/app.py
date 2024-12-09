from flask import Flask, render_template, request, jsonify
from ..models.ttng import TTNGModel
from ..models.narrative_context import NarrativeContext
from ..pipeline.graph_to_text import GraphToTextPipeline
from datetime import datetime, timedelta
import json
import os
import logging
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
        num_tracks = int(data.get('num_tracks', 3))
        num_timepoints = int(data.get('num_timepoints', 2))
        
        logger.info(f"Generating story with {num_tracks} tracks and {num_timepoints} timepoints")
        
        # Initialize the model and pipeline
        try:
            model = TTNGModel()
            pipeline = GraphToTextPipeline(model)
            context = pipeline.craft_narrative_context()
            logger.info("Successfully initialized model and pipeline")
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f"Failed to initialize model: {str(e)}"})
        
        base_time = datetime.now()
        story_data = {'nodes': [], 'edges': []}
        
        # Generate nodes for each timepoint and track
        for t in range(num_timepoints):
            for track in range(1, num_tracks + 1):
                try:
                    node_id = f"t{t+1}_track{track}"
                    logger.debug(f"Generating node {node_id}")
                    
                    # Create node context
                    node_context = pipeline.map_attributes(node_id, context)
                    model.add_node(node_id, base_time + timedelta(days=t), node_context, str(track))
                    logger.debug(f"Added node {node_id} to model")
                    
                    # Generate text for the node
                    text = pipeline.generate_text(model.nodes[node_id])
                    if not text:
                        raise ValueError(f"Generated text is empty for node {node_id}")
                    logger.debug(f"Generated text for node {node_id}: {text[:50]}...")
                    
                    story_data['nodes'].append({
                        'id': node_id,
                        'text': text,
                        'track': track,
                        'timepoint': t+1
                    })
                except Exception as e:
                    logger.error(f"Error generating node {node_id}: {str(e)}", exc_info=True)
                    return jsonify({
                        'success': False, 
                        'error': f"Failed to generate text for node {node_id}: {str(e)}"
                    })
        
        # Add edges between consecutive timepoints
        for t in range(num_timepoints - 1):
            for track in range(1, num_tracks + 1):
                from_node = f"t{t+1}_track{track}"
                to_node = f"t{t+2}_track{track}"
                model.add_edge(from_node, to_node)
                story_data['edges'].append({
                    'from': from_node,
                    'to': to_node
                })
                logger.debug(f"Added edge from {from_node} to {to_node}")
        
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