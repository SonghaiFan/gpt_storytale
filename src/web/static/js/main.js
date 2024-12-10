document.addEventListener('DOMContentLoaded', () => {
    // Initialize graph visualizer
    const visualizer = new TTNGVisualizer('graph-container');
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.id = 'node-tooltip';
    tooltip.className = 'tooltip';
    tooltip.style.display = 'none';
    tooltip.style.position = 'absolute';
    tooltip.style.backgroundColor = 'white';
    tooltip.style.border = '1px solid #ddd';
    tooltip.style.borderRadius = '4px';
    tooltip.style.padding = '10px';
    tooltip.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
    tooltip.style.zIndex = '1000';
    document.body.appendChild(tooltip);
    
    // Graph state
    let graphState = {
        nodes: new Map(),
        edges: new Set(),
        gridInitialized: false,
        genre: 'THREAD'  // Default genre
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
    const graphGenreSelect = document.getElementById('graph_genre');
    const genreDescription = document.getElementById('genre_description');
    
    // Update genre description when selection changes
    graphGenreSelect.addEventListener('change', () => {
        graphState.genre = graphGenreSelect.value;
        updateGenreDescription();
    });
    
    function updateGenreDescription() {
        const descriptions = {
            'THREAD': 'Each node can have at most 2 connections (1 in, 1 out)',
            'TREE': 'Each node can have at most 1 incoming connection',
            'MAP': 'No restrictions on connections between nodes'
        };
        genreDescription.textContent = descriptions[graphState.genre];
    }
    
    // Initialize grid
    function initializeGrid() {
        const numTracks = parseInt(numTracksInput.value);
        const numTimepoints = parseInt(numTimepointsInput.value);
        
        // Clear previous state
        graphState.nodes.clear();
        graphState.edges.clear();
        graphState.genre = graphGenreSelect.value;
        
        // Initialize visualization
        visualizer.initializeGrid(numTracks, numTimepoints, graphState.nodes);
        graphState.gridInitialized = true;
        
        // Update track and timepoint selectors
        updateTrackSelector(numTracks);
        updateTimepointSelector(numTimepoints);
        updateNodeSelectors();
        
        // Enable node editing
        addNodeBtn.disabled = false;
    }
    
    // Centralized constraint checker
    const GraphConstraints = {
        // Get node's connection counts
        getConnectionCounts(nodeId) {
            const outgoing = Array.from(graphState.edges).filter(edge => {
                const [src] = edge.split('->');
                return src === nodeId;
            }).length;
            
            const incoming = Array.from(graphState.edges).filter(edge => {
                const [, tgt] = edge.split('->');
                return tgt === nodeId;
            }).length;
            
            return { outgoing, incoming };
        },

        // Check if adding an edge would create a cycle
        wouldCreateCycle(fromId, toId) {
            const visited = new Set();
            const stack = [toId];
            
            while (stack.length > 0) {
                const currentId = stack.pop();
                if (currentId === fromId) return true;
                
                if (!visited.has(currentId)) {
                    visited.add(currentId);
                    Array.from(graphState.edges)
                        .filter(edge => edge.startsWith(`${currentId}->`))
                        .forEach(edge => {
                            const [, nextId] = edge.split('->');
                            stack.push(nextId);
                        });
                }
            }
            return false;
        },

        // Check temporal order
        isValidTemporalOrder(fromNode, toNode) {
            return fromNode.timepoint < toNode.timepoint;
        },

        // Check track adjacency
        isValidTrackDistance(fromNode, toNode) {
            return Math.abs(fromNode.track - toNode.track) <= 1;
        },

        // Get constraint violation reason for source node
        getSourceViolation(nodeId) {
            const counts = this.getConnectionCounts(nodeId);
            
            if (graphState.genre === 'THREAD' && counts.outgoing > 0) {
                return 'Thread genre: node already has an outgoing connection';
            }
            
            return null;
        },

        // Get constraint violation reason for target node
        getTargetViolation(fromId, toId) {
            if (!fromId) return null;
            
            const fromNode = graphState.nodes.get(fromId);
            const toNode = graphState.nodes.get(toId);
            const counts = this.getConnectionCounts(toId);

            if (fromId === toId) {
                return 'Cannot connect a node to itself';
            }

            if (!this.isValidTemporalOrder(fromNode, toNode)) {
                return 'Can only connect to later timepoints';
            }

            if (!this.isValidTrackDistance(fromNode, toNode)) {
                return 'Can only connect to adjacent tracks';
            }

            switch (graphState.genre) {
                case 'THREAD':
                    if (counts.incoming > 0) {
                        return 'Thread genre: node already has an incoming connection';
                    }
                    break;
                    
                case 'TREE':
                    if (counts.incoming > 0) {
                        return 'Tree genre: node already has a parent';
                    }
                    if (this.wouldCreateCycle(fromId, toId)) {
                        return 'Tree genre: this would create a cycle';
                    }
                    break;
            }
            
            return null;
        }
    };
    
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
            },
            isEmpty: false
        };
        
        graphState.nodes.set(nodeId, nodeData);
        visualizer.updateNode(nodeId, nodeData);
        updateNodeSelectors();
    }
    
    // Show tooltip for node
    function showTooltip(event, node) {
        if (!node) return;
        
        const rect = event.target.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        tooltip.innerHTML = `
            <h4>Node ${node.id}</h4>
            ${node.isEmpty ? '<p>Empty Node</p>' : `
                <p><span class="attribute-label">Entities:</span> ${node.attributes.entities.join(', ') || 'None'}</p>
                <p><span class="attribute-label">Events:</span> ${node.attributes.events.join(', ') || 'None'}</p>
                <p><span class="attribute-label">Topics:</span> ${node.attributes.topics.join(', ') || 'None'}</p>
            `}
        `;
        
        tooltip.style.display = 'block';
        tooltip.style.left = rect.left + scrollLeft + 'px';
        tooltip.style.top = rect.bottom + scrollTop + 5 + 'px';
    }
    
    // Hide tooltip
    function hideTooltip() {
        tooltip.style.display = 'none';
    }
    
    // Add event listeners for tooltip
    document.addEventListener('mouseover', (e) => {
        const nodeElement = e.target.closest('.node');
        if (nodeElement) {
            const nodeId = nodeElement.getAttribute('data-node-id');
            const nodeData = graphState.nodes.get(nodeId);
            showTooltip(e, nodeData);
        }
    });
    
    document.addEventListener('mouseout', (e) => {
        if (!e.target.closest('.node')) {
            hideTooltip();
        }
    });
    
    // Add edge between nodes
    function addEdge() {
        const fromId = edgeFromSelect.value;
        const toId = edgeToSelect.value;
        
        if (fromId && toId && fromId !== toId) {
            const edge = `${fromId}->${toId}`;
            if (!graphState.edges.has(edge)) {
                // Check if the edge would violate any constraints
                const violation = GraphConstraints.getTargetViolation(fromId, toId);
                if (!violation) {
                    graphState.edges.add(edge);
                    visualizer.addEdge(fromId, toId);
                    // Update node selectors to reflect new edge constraints
                    updateNodeSelectors();
                } else {
                    alert(violation);
                }
            }
        }
    }
    
    // Remove edge between nodes
    function removeEdge() {
        const fromId = edgeFromSelect.value;
        const toId = edgeToSelect.value;
        
        if (fromId && toId) {
            const edge = `${fromId}->${toId}`;
            if (graphState.edges.has(edge)) {
                graphState.edges.delete(edge);
                visualizer.removeEdge(fromId, toId);
                // Update node selectors to reflect removed edge
                updateNodeSelectors();
            }
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
        const nodes = Array.from(graphState.nodes.entries());
        
        // Update source node selector
        edgeFromSelect.innerHTML = '<option value="">Select source node</option>';
        nodes.forEach(([nodeId, data]) => {
            const option = document.createElement('option');
            option.value = nodeId;
            option.textContent = nodeId;
            
            const violation = GraphConstraints.getSourceViolation(nodeId);
            if (violation) {
                option.disabled = true;
                option.title = violation;
            }
            
            edgeFromSelect.appendChild(option);
        });

        // Update target node selector based on selected source
        function updateTargetSelector() {
            const selectedSource = edgeFromSelect.value;
            
            edgeToSelect.innerHTML = '<option value="">Select target node</option>';
            nodes.forEach(([nodeId, data]) => {
                const option = document.createElement('option');
                option.value = nodeId;
                option.textContent = nodeId;
                
                const violation = GraphConstraints.getTargetViolation(selectedSource, nodeId);
                if (violation) {
                    option.disabled = true;
                    option.title = violation;
                }
                
                edgeToSelect.appendChild(option);
            });
        }

        // Add change listener to source selector
        edgeFromSelect.addEventListener('change', updateTargetSelector);
        
        // Initial update of target selector
        updateTargetSelector();
        
        // Enable/disable edge buttons based on available options
        const hasValidSourceOptions = Array.from(edgeFromSelect.options).some(opt => !opt.disabled && opt.value);
        const hasValidTargetOptions = Array.from(edgeToSelect.options).some(opt => !opt.disabled && opt.value);
        addEdgeBtn.disabled = !hasValidSourceOptions || !hasValidTargetOptions;
        removeEdgeBtn.disabled = !hasValidSourceOptions || !hasValidTargetOptions;
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
    
    // Initialize genre description
    updateGenreDescription();
}); 