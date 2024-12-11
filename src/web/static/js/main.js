document.addEventListener('DOMContentLoaded', () => {
    // Initialize graph visualizer
    const visualizer = new TTNGVisualizer('graph-container');
    
    
    // Graph state
    let graphState = {
        nodes: new Map(),
        edges: new Set(),
        gridInitialized: false,
        idiom: 'THREAD',  // Default idiom
        selectedNodeId: null,  // Track currently selected node
        selectedEdge: null     // Track currently selected edge
    };
    
    // Button configuration
    const buttonConfig = {
        init_grid_btn: {
            text: 'Initialize Grid',
            className: 'primary-btn',
            onClick: initializeGrid
        },
        add_node_btn: {
            text: 'Add Node',
            className: 'secondary-btn',
            onClick: updateNode
        },
        clear_node_btn: {
            text: 'Clear Selection',
            className: 'secondary-btn',
            onClick: clearNodeEditor,
            insertAfter: 'add_node_btn'
        },
        add_edge_btn: {
            text: 'Add Edge',
            className: 'secondary-btn',
            onClick: addEdge
        },
        remove_edge_btn: {
            text: 'Remove Edge',
            className: 'danger-btn',
            onClick: removeEdge
        },
        generate_btn: {
            text: 'Generate Story',
            className: 'primary-btn',
            onClick: generateStory
        },
        clear_graph_btn: {
            text: 'Clear Graph',
            className: 'danger-btn',
            onClick: () => {
                if (confirm('Are you sure you want to clear the graph?')) {
                    initializeGrid();
                }
            }
        }
    };
    
    // Helper function to create or setup buttons
    function setupButton(id, config) {
        let button = document.getElementById(id);
        if (!button) {
            // Create button if it doesn't exist
            button = document.createElement('button');
            button.id = id;
            
            // Insert after specified element or at the end of its section
            if (config.insertAfter) {
                const referenceBtn = document.getElementById(config.insertAfter);
                referenceBtn.parentNode.insertBefore(button, referenceBtn.nextSibling);
            }
        }
        
        // Setup button properties
        button.textContent = config.text;
        button.className = config.className;
        button.onclick = config.onClick;
        if (config.disabled) {
            button.disabled = true;
        }
        
        return button;
    }
    
    // Initialize all buttons
    const buttons = {};
    for (const [id, config] of Object.entries(buttonConfig)) {
        buttons[id] = setupButton(id, config);
    }
    
    // Get DOM elements
    const nodeTrackSelect = document.getElementById('node_track');
    const nodeTimepointSelect = document.getElementById('node_timepoint');
    const nodeEntityInput = document.getElementById('node_entity');
    const nodeEventInput = document.getElementById('node_event');
    const nodeTopicInput = document.getElementById('node_topic');
    const edgeFromSelect = document.getElementById('edge_from');
    const edgeToSelect = document.getElementById('edge_to');
    const numTracksInput = document.getElementById('num_tracks');
    const numTimepointsInput = document.getElementById('num_timepoints');
    const organizingAttributeSelect = document.getElementById('organizing_attribute');
    const graphIdiomSelect = document.getElementById('graph_idiom');
    const idiomDescription = document.getElementById('idiom_description');
    const tooltip = document.getElementById('node-tooltip')
    
    // Disable edge buttons initially
    buttons.add_edge_btn.disabled = true;
    buttons.remove_edge_btn.disabled = true;
    
    // Update idiom description when selection changes
    graphIdiomSelect.addEventListener('change', () => {
        graphState.idiom = graphIdiomSelect.value;
        updateIdiomDescription();
    });
    
    function updateIdiomDescription() {
        const descriptions = {
            'THREAD': 'Each node can have at most 2 connections (1 in, 1 out)',
            'TREE': 'Each node can have at most 1 incoming connection',
            'MAP': 'No restrictions on connections between nodes'
        };
        idiomDescription.textContent = descriptions[graphState.idiom];
    }
    
    // Add node selection handler to visualizer
    function handleNodeClick(nodeId) {
        // Deselect if clicking the same node
        if (graphState.selectedNodeId === nodeId) {
            graphState.selectedNodeId = null;
            clearNodeEditor();
            visualizer.setSelectedNode(null);
        } else {
            graphState.selectedNodeId = nodeId;
            const nodeData = graphState.nodes.get(nodeId);
            
            // Extract track and timepoint from nodeId (format: t{timepoint}_track{track})
            const [timepoint, track] = nodeId.match(/t(\d+)_track(\d+)/).slice(1).map(Number);
            
            // If node is empty, populate editor with position only
            if (!nodeData || nodeData.isEmpty) {
                nodeTrackSelect.value = track;
                nodeTimepointSelect.value = timepoint;
                nodeEntityInput.value = '';
                nodeEventInput.value = '';
                nodeTopicInput.value = '';
                buttons.add_node_btn.textContent = 'Add Node';
                buttons.clear_node_btn.disabled = false;
            } else {
                // Populate with existing node data
                populateNodeEditor(nodeData);
            }
            
            visualizer.setSelectedNode(nodeId);
        }
    }
    
    // Add edge selection handler
    function handleEdgeClick(edgeString) {
        const [fromId, toId] = edgeString.split('->');
        if (graphState.selectedEdge === edgeString) {
            graphState.selectedEdge = null;
            clearEdgeEditor();
            visualizer.setSelectedEdge(null);
        } else {
            graphState.selectedEdge = edgeString;
            edgeFromSelect.value = fromId;
            edgeToSelect.value = toId;
            visualizer.setSelectedEdge(edgeString);
        }
    }
    
    // Populate node editor with node data
    function populateNodeEditor(nodeData) {
        if (!nodeData) {
            clearNodeEditor();
            return;
        }
        
        nodeTrackSelect.value = nodeData.track;
        nodeTimepointSelect.value = nodeData.timepoint;
        nodeEntityInput.value = nodeData.attributes?.entities?.join(', ') || '';
        nodeEventInput.value = nodeData.attributes?.events?.join(', ') || '';
        nodeTopicInput.value = nodeData.attributes?.topics?.join(', ') || '';
        
        // Update button states
        buttons.add_node_btn.textContent = nodeData.isEmpty ? 'Add Node' : 'Update Node';
        buttons.clear_node_btn.disabled = false;
    }
    
    // Clear node editor
    function clearNodeEditor(keepValues = false) {
        if (!keepValues) {
            nodeEntityInput.value = '';
            nodeEventInput.value = '';
            nodeTopicInput.value = '';
        }
        buttons.add_node_btn.textContent = 'Add Node';
        buttons.clear_node_btn.disabled = true;
        graphState.selectedNodeId = null;
        visualizer.setSelectedNode(null);
    }
    
    // Clear edge editor
    function clearEdgeEditor() {
        edgeFromSelect.value = '';
        edgeToSelect.value = '';
        graphState.selectedEdge = null;
    }
    
    // Update node in graph
    function updateNode() {
        const track = nodeTrackSelect.value;
        const timepoint = nodeTimepointSelect.value;
        const nodeId = graphState.selectedNodeId || `t${timepoint}_track${track}`;
        
        // Get raw input values first
        const entityValue = nodeEntityInput.value.trim();
        const eventValue = nodeEventInput.value.trim();
        const topicValue = nodeTopicInput.value.trim();

        // Ensure at least one value for each attribute
        if (!entityValue || !eventValue || !topicValue) {
            alert('Please provide at least one value for each of: Entity, Event, and Topic');
            return;
        }

        // Split comma-separated values and trim whitespace
        const entities = entityValue ? entityValue.split(',').map(s => s.trim()).filter(Boolean) : [];
        const events = eventValue ? eventValue.split(',').map(s => s.trim()).filter(Boolean) : [];
        const topics = topicValue ? topicValue.split(',').map(s => s.trim()).filter(Boolean) : [];

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
        
        // Pass true to keep the input values
        clearNodeEditor(true);
    }
    
    // Show tooltip for node
    function showTooltip(event, node) {
        if (!node) return;
        
        const rect = event.target.getBoundingClientRect();
        const scrollTop =  document.documentElement.scrollTop;
        const scrollLeft = document.documentElement.scrollLeft;
        
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
        const fromNode = edgeFromSelect.value;
        const toNode = edgeToSelect.value;
        
        if (fromNode && toNode && fromNode !== toNode) {
            if (validateEdge(fromNode, toNode)) {
                const edge = `${fromNode}->${toNode}`;
                graphState.edges.add(edge);
                visualizer.addEdge(fromNode, toNode);
            }
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
        buttons.add_edge_btn.disabled = !hasNodes;
        buttons.remove_edge_btn.disabled = !hasNodes;
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
            buttons.generate_btn.disabled = true;
            buttons.generate_btn.textContent = 'Generating...';
            
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
            buttons.generate_btn.disabled = false;
            buttons.generate_btn.textContent = 'Generate Story';
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
        buttons.add_node_btn.disabled = true;
        buttons.add_edge_btn.disabled = true;
        buttons.remove_edge_btn.disabled = true;
    }
    
    // Initialize grid
    function initializeGrid() {
        const numTracks = parseInt(numTracksInput.value);
        const numTimepoints = parseInt(numTimepointsInput.value);
        
        // Clear previous state
        graphState.nodes.clear();
        graphState.edges.clear();
        graphState.selectedNodeId = null;
        graphState.selectedEdge = null;
        graphState.idiom = graphIdiomSelect.value;
        
        // Initialize visualization
        visualizer.initializeGrid(numTracks, numTimepoints, graphState.nodes);
        visualizer.setNodeClickHandler(handleNodeClick);
        visualizer.setEdgeClickHandler(handleEdgeClick);
        graphState.gridInitialized = true;
        
        // Update selectors and clear editors
        updateTrackSelector(numTracks);
        updateTimepointSelector(numTimepoints);
        updateNodeSelectors();
        clearNodeEditor();
        clearEdgeEditor();
        
        // Enable node editing
        buttons.add_node_btn.disabled = false;
    }
    
    // Validate edge based on idiom constraints
    function validateEdge(fromId, toId) {
        // Get nodes involved in the edge
        const fromNode = graphState.nodes.get(fromId);
        const toNode = graphState.nodes.get(toId);
        
        if (!fromNode || !toNode) {
            alert('Invalid nodes selected');
            return false;
        }

        // Check if edge already exists
        if (graphState.edges.has(`${fromId}->${toId}`)) {
            alert('This edge already exists');
            return false;
        }

        // Check temporal order
        if (fromNode.timepoint >= toNode.timepoint) {
            alert('Invalid connection: Edges must flow forward in time (from earlier to later timepoints)');
            return false;
        }

        // Count existing connections
        const getNodeConnections = (nodeId) => {
            const outgoing = Array.from(graphState.edges)
                .filter(edge => edge.startsWith(`${nodeId}->`)).length;
            const incoming = Array.from(graphState.edges)
                .filter(edge => edge.endsWith(`->${nodeId}`)).length;
            return { outgoing, incoming };
        };

        const fromConnections = getNodeConnections(fromId);
        const toConnections = getNodeConnections(toId);

        // Apply idiom-specific constraints
        switch (graphState.idiom) {
            case 'THREAD':
                // In THREAD idiom, each node can only have one incoming and one outgoing connection
                if (fromConnections.outgoing > 0) {
                    alert('Thread idiom: The source node already has an outgoing connection. In Thread idiom, each node can only have one outgoing connection.');
                    return false;
                }
                if (toConnections.incoming > 0) {
                    alert('Thread idiom: The target node already has an incoming connection. In Thread idiom, each node can only have one incoming connection.');
                    return false;
                }
                break;

            case 'TREE':
                // In TREE idiom, each node can have multiple outgoing but only one incoming connection
                if (toConnections.incoming > 0) {
                    alert('Tree idiom: The target node already has an incoming connection. In Tree idiom, each node can only have one parent (incoming connection).');
                    return false;
                }

                // Check for cycles
                if (wouldCreateCycle(fromId, toId)) {
                    alert('Tree idiom: This connection would create a cycle, which is not allowed in a tree structure.');
                    return false;
                }
                break;

            case 'MAP':
                // MAP idiom has no additional connection constraints
                break;
        }

        return true;
    }

    // Helper function to check if adding an edge would create a cycle
    function wouldCreateCycle(fromId, toId) {
        const visited = new Set();
        const stack = [toId];
        
        while (stack.length > 0) {
            const currentId = stack.pop();
            
            if (currentId === fromId) {
                return true; // Would create a cycle
            }
            
            if (!visited.has(currentId)) {
                visited.add(currentId);
                // Add all nodes that this node connects to
                Array.from(graphState.edges)
                    .filter(edge => edge.startsWith(`${currentId}->`))
                    .forEach(edge => {
                        const [, nextId] = edge.split('->');
                        stack.push(nextId);
                    });
            }
        }
        
        return false;
    }
    
    // Event listeners
    buttons.init_grid_btn.addEventListener('click', initializeGrid);
    buttons.add_node_btn.addEventListener('click', updateNode);
    buttons.add_edge_btn.addEventListener('click', addEdge);
    buttons.remove_edge_btn.addEventListener('click', removeEdge);
    buttons.generate_btn.addEventListener('click', generateStory);
    buttons.clear_graph_btn.addEventListener('click', clearGraph);
    
    // Initialize button states
    buttons.add_node_btn.disabled = true;
    buttons.add_edge_btn.disabled = true;
    buttons.remove_edge_btn.disabled = true;
    
    // Initialize idiom description
    updateIdiomDescription();
}); 