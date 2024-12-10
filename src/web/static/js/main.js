document.addEventListener('DOMContentLoaded', () => {
    // Initialize graph visualizer
    const visualizer = new TTNGVisualizer('graph-container');
    
    // Graph state
    let graphState = {
        nodes: new Map(),
        edges: new Set(),
        gridInitialized: false
    };
    
    // Get DOM elements
    const initGridBtn = document.getElementById('init_grid_btn');
    const addNodeBtn = document.getElementById('add_node_btn');
    const addEdgeBtn = document.getElementById('add_edge_btn');
    const removeEdgeBtn = document.getElementById('remove_edge_btn');
    const generateBtn = document.getElementById('generate_btn');
    const clearGraphBtn = document.getElementById('clear_graph_btn');
    
    // Node editor elements
    const nodeTrackSelect = document.getElementById('node_track');
    const nodeTimepointSelect = document.getElementById('node_timepoint');
    const nodeEntityInput = document.getElementById('node_entity');
    const nodeEventInput = document.getElementById('node_event');
    const nodeTopicInput = document.getElementById('node_topic');
    
    // Edge editor elements
    const edgeFromSelect = document.getElementById('edge_from');
    const edgeToSelect = document.getElementById('edge_to');
    
    // Grid settings elements
    const numTracksInput = document.getElementById('num_tracks');
    const numTimepointsInput = document.getElementById('num_timepoints');
    const organizingAttributeSelect = document.getElementById('organizing_attribute');
    
    // Initialize grid
    function initializeGrid() {
        const numTracks = parseInt(numTracksInput.value);
        const numTimepoints = parseInt(numTimepointsInput.value);
        
        // Clear previous state
        graphState.nodes.clear();
        graphState.edges.clear();
        
        // Initialize empty grid visualization
        visualizer.initializeGrid(numTracks, numTimepoints);
        graphState.gridInitialized = true;
        
        // Update track and timepoint selectors
        updateTrackSelector(numTracks);
        updateTimepointSelector(numTimepoints);
        updateNodeSelectors();
        
        // Enable node editing
        addNodeBtn.disabled = false;
    }
    
    // Update node in graph
    function updateNode() {
        const track = nodeTrackSelect.value;
        const timepoint = nodeTimepointSelect.value;
        const nodeId = `t${timepoint}_track${track}`;
        
        // Split comma-separated values and trim whitespace
        const entities = nodeEntityInput.value ? nodeEntityInput.value.split(',').map(s => s.trim()).filter(s => s) : [];
        const events = nodeEventInput.value ? nodeEventInput.value.split(',').map(s => s.trim()).filter(s => s) : [];
        const topics = nodeTopicInput.value ? nodeTopicInput.value.split(',').map(s => s.trim()).filter(s => s) : [];
        
        // Ensure at least one value for each attribute
        if (!entities.length || !events.length || !topics.length) {
            alert('Please provide at least one value for each of: Entity, Event, and Topic');
            return;
        }
        
        const nodeData = {
            id: nodeId,
            track: parseInt(track),
            timepoint: parseInt(timepoint),
            attributes: {
                entities: entities,
                events: events,
                topics: topics
            }
        };
        
        graphState.nodes.set(nodeId, nodeData);
        visualizer.updateNode(nodeId, nodeData.attributes);
        updateNodeSelectors();
    }
    
    // Add edge between nodes
    function addEdge() {
        const fromNode = edgeFromSelect.value;
        const toNode = edgeToSelect.value;
        
        if (fromNode && toNode && fromNode !== toNode) {
            const edge = `${fromNode}->${toNode}`;
            graphState.edges.add(edge);
            visualizer.addEdge(fromNode, toNode);
        }
    }
    
    // Remove edge between nodes
    function removeEdge() {
        const fromNode = edgeFromSelect.value;
        const toNode = edgeToSelect.value;
        
        if (fromNode && toNode) {
            const edge = `${fromNode}->${toNode}`;
            graphState.edges.delete(edge);
            visualizer.removeEdge(fromNode, toNode);
        }
    }
    
    // Update track selector options
    function updateTrackSelector(numTracks) {
        nodeTrackSelect.innerHTML = '';
        for (let i = 1; i <= numTracks; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `Track ${i}`;
            nodeTrackSelect.appendChild(option);
        }
    }
    
    // Update timepoint selector options
    function updateTimepointSelector(numTimepoints) {
        nodeTimepointSelect.innerHTML = '';
        for (let i = 1; i <= numTimepoints; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `T${i}`;
            nodeTimepointSelect.appendChild(option);
        }
    }
    
    // Update node selectors for edges
    function updateNodeSelectors() {
        const nodes = Array.from(graphState.nodes.keys());
        
        [edgeFromSelect, edgeToSelect].forEach(select => {
            const currentValue = select.value;
            select.innerHTML = '';
            
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a node';
            select.appendChild(defaultOption);
            
            nodes.forEach(nodeId => {
                const option = document.createElement('option');
                option.value = nodeId;
                option.textContent = nodeId;
                select.appendChild(option);
            });
            
            if (nodes.includes(currentValue)) {
                select.value = currentValue;
            }
        });
        
        // Enable/disable edge buttons based on node count
        const hasNodes = nodes.length >= 2;
        addEdgeBtn.disabled = !hasNodes;
        removeEdgeBtn.disabled = !hasNodes;
    }
    
    // Generate story from graph
    async function generateStory() {
        try {
            const graphData = {
                nodes: Array.from(graphState.nodes.values()),
                edges: Array.from(graphState.edges).map(edge => {
                    const [from, to] = edge.split('->');
                    return { from, to };
                })
            };
            
            // Disable button and show loading state
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
            
            // Make API request
            const response = await fetch('/generate_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    graph: graphData,
                    organizing_attribute: organizingAttributeSelect.value.toLowerCase(),
                    style: {
                        cefr_level: 'B2',
                        tone: 'neutral'
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate story');
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to generate story');
            }
            
            // Display the story
            const storyContent = document.getElementById('story-content');
            storyContent.innerHTML = '';
            data.story.nodes.forEach(node => {
                const storyDiv = document.createElement('div');
                storyDiv.className = 'story-segment';
                storyDiv.innerHTML = `
                    <h3>Track ${node.track} - Timepoint ${node.timepoint}</h3>
                    <p>${node.text}</p>
                `;
                storyContent.appendChild(storyDiv);
            });
            
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to generate story. Please try again.');
        } finally {
            // Reset button state
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Story';
        }
    }
    
    // Clear graph
    function clearGraph() {
        graphState.nodes.clear();
        graphState.edges.clear();
        graphState.gridInitialized = false;
        
        // Clear inputs
        nodeEntityInput.value = '';
        nodeEventInput.value = '';
        nodeTopicInput.value = '';
        
        // Reset selectors
        updateNodeSelectors();
        
        // Clear visualization
        const numTracks = parseInt(numTracksInput.value);
        const numTimepoints = parseInt(numTimepointsInput.value);
        visualizer.initializeGrid(numTracks, numTimepoints);
        
        // Clear story
        document.getElementById('story-content').innerHTML = '';
        
        // Disable buttons
        addNodeBtn.disabled = true;
        addEdgeBtn.disabled = true;
        removeEdgeBtn.disabled = true;
    }
    
    // Event listeners
    initGridBtn.addEventListener('click', initializeGrid);
    addNodeBtn.addEventListener('click', updateNode);
    addEdgeBtn.addEventListener('click', addEdge);
    removeEdgeBtn.addEventListener('click', removeEdge);
    generateBtn.addEventListener('click', generateStory);
    clearGraphBtn.addEventListener('click', clearGraph);
    
    // Initialize button states
    addNodeBtn.disabled = true;
    addEdgeBtn.disabled = true;
    removeEdgeBtn.disabled = true;
}); 