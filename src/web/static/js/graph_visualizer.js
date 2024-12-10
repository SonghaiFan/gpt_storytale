class TTNGVisualizer {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = this.container.node().getBoundingClientRect().height;
        this.margin = { top: 60, right: 40, bottom: 60, left: 80 };
        this.nodeRadius = 20;
        
        this.svg = this.container.append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, this.width, this.height]);
        
        // Initialize all groups in correct order (back to front)
        this.gridGroup = this.svg.append('g').attr('class', 'grid');
        this.axisGroup = this.svg.append('g').attr('class', 'axes');
        this.zoomGroup = this.svg.append('g').attr('class', 'zoom-group');
        
        // Create groups in correct order within zoom group
        this.trackGroup = this.zoomGroup.append('g').attr('class', 'tracks');
        this.edgeGroup = this.zoomGroup.append('g')
            .attr('class', 'edges')
            .style('pointer-events', 'all');  // Enable pointer events
        this.nodeGroup = this.zoomGroup.append('g').attr('class', 'nodes');
        
        // Initialize axis groups
        this.xAxisGroup = this.axisGroup.append('g').attr('class', 'x-axis');
        this.yAxisGroup = this.axisGroup.append('g').attr('class', 'y-axis');
        
        // Define style constants
        this.styles = {
            node: {
                empty: {
                    fill: '#fff',
                    stroke: '#adb5bd',
                    strokeWidth: 2,
                    strokeDasharray: '5,5'  // Add dashed border for empty nodes
                },
                filled: {
                    fill: '#fff',
                    stroke: '#000',
                    strokeWidth: 2,
                    strokeDasharray: null  // Solid border for filled nodes
                },
                hover: {
                    stroke: '#339af0',
                    strokeWidth: 3,
                    strokeDasharray: null  // Keep solid border on hover
                },
                selected: {
                    stroke: '#1c7ed6',
                    strokeWidth: 3,
                    shadow: true,
                    strokeDasharray: null  // Keep solid border when selected
                }
            },
            edge: {
                default: {
                    stroke: '#000',
                    strokeWidth: 2,
                    markerEnd: 'url(#arrow)'
                },
                hover: {
                    stroke: '#339af0',
                    strokeWidth: 2,
                    markerEnd: 'url(#arrow-hover)'
                },
                selected: {
                    stroke: '#1c7ed6',
                    strokeWidth: 3,
                    markerEnd: 'url(#arrow-selected)'
                }
            }
        };

        // Add drop shadow filter for selected nodes
        const defs = this.svg.append('defs');
        
        // Add drop shadow filter
        const filter = defs.append('filter')
            .attr('id', 'drop-shadow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');  // Increased filter area

        filter.append('feGaussianBlur')
            .attr('in', 'SourceAlpha')
            .attr('stdDeviation', 2)  // Reduced blur for softer edge
            .attr('result', 'blur');

        filter.append('feOffset')
            .attr('in', 'blur')
            .attr('dx', 0)  // Removed horizontal offset
            .attr('dy', 1)  // Slight vertical offset
            .attr('result', 'offsetBlur');

        // Add color matrix to make shadow more transparent
        filter.append('feColorMatrix')
            .attr('in', 'offsetBlur')
            .attr('type', 'matrix')
            .attr('values', '0 0 0 0 0   0 0 0 0 0   0 0 0 0 0  0 0 0 0.3 0')  // Last value controls opacity
            .attr('result', 'coloredBlur');

        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode')
            .attr('in', 'coloredBlur');
        feMerge.append('feMergeNode')
            .attr('in', 'SourceGraphic');

        // Add arrow markers
        // Default arrow
        defs.append('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 8)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', this.styles.edge.default.stroke);

        // Hover arrow
        defs.append('marker')
            .attr('id', 'arrow-hover')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 8)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', this.styles.edge.hover.stroke);

        // Selected arrow
        defs.append('marker')
            .attr('id', 'arrow-selected')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 8)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', this.styles.edge.selected.stroke);
        
        this.nodes = new Map();
        this.edges = new Set();
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.5, 2])
            .on('zoom', (event) => this._handleZoom(event));
        
        this.svg.call(zoom);
        
        this.nodeClickHandler = null;
        this.edgeClickHandler = null;
        this.selectedNodeId = null;
        this.selectedEdge = null;
    }
    
    _handleZoom(event) {
        const transform = event.transform;
        
        // Transform the main content
        this.zoomGroup.attr('transform', transform);
        
        // Update axes and grid
        if (this.xScale && this.yScale) {
            const newXScale = transform.rescaleX(this.xScale);
            const newYScale = transform.rescaleY(this.yScale);
            
            // Update axes
            this.xAxisGroup.call(this.xAxis.scale(newXScale));
            this.yAxisGroup.call(this.yAxis.scale(newYScale));
            
            // Update grid lines
            this.gridGroup.call(this.updateGrid.bind(this, newXScale, newYScale));
        }
    }
    
    updateGrid(xScale, yScale) {
        // Update vertical grid lines
        const verticalGrid = this.gridGroup.selectAll('.vertical-grid')
            .data(xScale.ticks());
            
        verticalGrid.exit().remove();
        
        verticalGrid.enter()
            .append('line')
            .attr('class', 'vertical-grid')
            .merge(verticalGrid)
            .attr('x1', d => xScale(d))
            .attr('x2', d => xScale(d))
            .attr('y1', this.margin.top)
            .attr('y2', this.height - this.margin.bottom)
            .attr('stroke', '#e9ecef')
            .attr('stroke-width', 1)
            .attr('stroke-dasharray', '4');
            
        // Update horizontal grid lines
        const horizontalGrid = this.gridGroup.selectAll('.horizontal-grid')
            .data(yScale.ticks());
            
        horizontalGrid.exit().remove();
        
        horizontalGrid.enter()
            .append('line')
            .attr('class', 'horizontal-grid')
            .merge(horizontalGrid)
            .attr('x1', this.margin.left)
            .attr('x2', this.width - this.margin.right)
            .attr('y1', d => yScale(d))
            .attr('y2', d => yScale(d))
            .attr('stroke', '#e9ecef')
            .attr('stroke-width', 1)
            .attr('stroke-dasharray', '4');
    }
    
    initializeGrid(numTracks, numTimepoints, nodes) {
        this.clear();
        
        const contentWidth = this.width - this.margin.left - this.margin.right;
        const contentHeight = this.height - this.margin.top - this.margin.bottom;
        
        // Calculate track dimensions
        const nodeSpacing = 20;
        const trackHeight = this.nodeRadius * 2 + nodeSpacing * 2;
        const trackPadding = 40;
        
        // Create base scales
        this.xScale = d3.scaleLinear()
            .domain([0.5, numTimepoints + 0.5])
            .range([this.margin.left, this.width - this.margin.right]);
            
        this.yScale = d3.scaleLinear()
            .domain([0.5, numTracks + 0.5])
            .range([this.margin.top, this.height - this.margin.bottom]);
        
        // Create axes
        this.xAxis = d3.axisTop(this.xScale)
            .ticks(numTimepoints)
            .tickFormat(d => Number.isInteger(d) ? `T${d}` : '');
            
        this.yAxis = d3.axisLeft(this.yScale)
            .ticks(numTracks)
            .tickFormat(d => Number.isInteger(d) ? `Track ${d}` : '');
        
        // Add axes
        this.xAxisGroup
            .attr('transform', `translate(0,${this.margin.top})`)
            .call(this.xAxis);
        
        this.yAxisGroup
            .attr('transform', `translate(${this.margin.left},0)`)
            .call(this.yAxis);
        
        // Add initial grid
        this.updateGrid(this.xScale, this.yScale);
        
        // Draw tracks
        for (let track = 1; track <= numTracks; track++) {
            const y = this.yScale(track);
            
            // Draw track background
            this.trackGroup.append('rect')
                .attr('class', 'track-bg')
                .attr('x', this.margin.left + nodeSpacing)
                .attr('y', y - trackHeight/2)
                .attr('width', contentWidth - nodeSpacing * 2)
                .attr('height', trackHeight)
                .attr('rx', trackHeight/2)
                .attr('ry', trackHeight/2)
                .attr('fill', '#f8f9fa')
                .attr('stroke', '#e9ecef');
            
            // Add nodes for this track
            for (let timepoint = 1; timepoint <= numTimepoints; timepoint++) {
                const x = this.xScale(timepoint);
                const nodeId = `t${timepoint}_track${track}`;
                const nodeData = nodes.get(nodeId) || { isEmpty: true };
                
                this.nodes.set(nodeId, { x, y, ...nodeData });
            }
        }
        
        this._updateVisualization();
    }
    
    clear() {
        // Clear data structures
        this.nodes.clear();
        this.edges.clear();
        
        // Clear all group contents
        if (this.gridGroup) this.gridGroup.selectAll('*').remove();
        if (this.trackGroup) this.trackGroup.selectAll('*').remove();
        if (this.edgeGroup) this.edgeGroup.selectAll('*').remove();
        if (this.nodeGroup) this.nodeGroup.selectAll('*').remove();
        if (this.xAxisGroup) this.xAxisGroup.selectAll('*').remove();
        if (this.yAxisGroup) this.yAxisGroup.selectAll('*').remove();
    }
    
    updateNode(nodeId, nodeData) {
        if (this.nodes.has(nodeId)) {
            const node = this.nodes.get(nodeId);
            this.nodes.set(nodeId, { ...node, ...nodeData });
            this._updateVisualization();
        }
    }
    
    addEdge(fromId, toId) {
        this.edges.add(`${fromId}->${toId}`);
        this._updateVisualization();
    }
    
    removeEdge(fromId, toId) {
        this.edges.delete(`${fromId}->${toId}`);
        this._updateVisualization();
    }
    
    setNodeClickHandler(handler) {
        this.nodeClickHandler = handler;
    }

    setEdgeClickHandler(handler) {
        this.edgeClickHandler = handler;
    }

    setSelectedNode(nodeId) {
        this.selectedNodeId = nodeId;
        this._updateVisualization();
    }

    setSelectedEdge(edgeString) {
        this.selectedEdge = edgeString;
        this._updateVisualization();
    }
    
    _calculateEdgePath(source, target) {
        // Calculate the angle between nodes
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const angle = Math.atan2(dy, dx);
        
        // Calculate where the edge should start and end considering node radius
        const startX = source.x + (this.nodeRadius * Math.cos(angle));
        const startY = source.y + (this.nodeRadius * Math.sin(angle));
        const endX = target.x - (this.nodeRadius * Math.cos(angle));
        const endY = target.y - (this.nodeRadius * Math.sin(angle));
        
        return `M${startX},${startY}L${endX},${endY}`;
    }
    
    _updateVisualization() {
        console.log('Updating visualization');
        
        // Update edges
        const edgeElements = this.edgeGroup
            .selectAll('.edge')
            .data(Array.from(this.edges), d => d);
        
        edgeElements.exit().remove();
        
        // Create new edges
        const edgeEnter = edgeElements.enter()
            .append('path')
            .attr('class', 'edge')
            .attr('fill', 'none')
            .style('cursor', 'pointer')
            .style('pointer-events', 'all');

        // Update all edges
        const allEdges = edgeElements.merge(edgeEnter)
            .attr('d', edge => {
                const [fromId, toId] = edge.split('->');
                const source = this.nodes.get(fromId);
                const target = this.nodes.get(toId);
                return this._calculateEdgePath(source, target);
            });

        // Apply edge styles
        this._applyEdgeStyles(allEdges);

        // Add edge interactions
        allEdges
            .on('mouseenter', (event, d) => {
                if (d !== this.selectedEdge) {
                    const edge = d3.select(event.currentTarget);
                    this._applyEdgeState(edge, 'hover');
                }
            })
            .on('mouseleave', (event, d) => {
                if (d !== this.selectedEdge) {
                    const edge = d3.select(event.currentTarget);
                    this._applyEdgeState(edge, 'default');
                }
            })
            .on('click', (event, d) => {
                if (this.edgeClickHandler) {
                    this.edgeClickHandler(d);
                }
            });

        // Update nodes
        const nodeElements = this.nodeGroup
            .selectAll('.node')
            .data(Array.from(this.nodes.entries()), d => d[0]);
        
        nodeElements.exit().remove();
        
        const nodeEnter = nodeElements.enter()
            .append('g')
            .attr('class', 'node')
            .attr('data-node-id', d => d[0])
            .style('cursor', 'pointer');

        nodeEnter.append('circle')
            .attr('r', this.nodeRadius);

        const allNodes = nodeElements.merge(nodeEnter)
            .attr('transform', d => `translate(${d[1].x},${d[1].y})`);

        // Apply node styles
        this._applyNodeStyles(allNodes);

        // Add node interactions
        allNodes
            .on('mouseenter', (event, d) => {
                if (d[0] !== this.selectedNodeId) {
                    const node = d3.select(event.currentTarget);
                    this._applyNodeState(node, d[1], 'hover');
                }
            })
            .on('mouseleave', (event, d) => {
                if (d[0] !== this.selectedNodeId) {
                    const node = d3.select(event.currentTarget);
                    this._applyNodeState(node, d[1], d[1].isEmpty ? 'empty' : 'filled');
                }
            })
            .on('click', (event, d) => {
                if (this.nodeClickHandler) {
                    this.nodeClickHandler(d[0]);
                }
            });
    }

    _applyNodeStyles(nodes) {
        nodes.each((d, i, elements) => {
            const node = d3.select(elements[i]);
            const state = d[0] === this.selectedNodeId ? 'selected' : 
                         d[1].isEmpty ? 'empty' : 'filled';
            this._applyNodeState(node, d[1], state);
        });
    }

    _applyNodeState(node, data, state) {
        const circle = node.select('circle');
        const style = this.styles.node[state];
        
        circle
            .attr('fill', style.fill || (data.isEmpty ? '#fff' : '#fff'))
            .attr('stroke', style.stroke)
            .attr('stroke-width', style.strokeWidth)
            .attr('stroke-dasharray', style.strokeDasharray)  // Apply dash array
            .style('filter', style.shadow ? 'url(#drop-shadow)' : null);
    }

    _applyEdgeStyles(edges) {
        edges.each((d, i, elements) => {
            const edge = d3.select(elements[i]);
            const state = d === this.selectedEdge ? 'selected' : 'default';
            this._applyEdgeState(edge, state);
        });
    }

    _applyEdgeState(edge, state) {
        const style = this.styles.edge[state];
        edge
            .attr('stroke', style.stroke)
            .attr('stroke-width', style.strokeWidth)
            .attr('marker-end', style.markerEnd);
    }
}

// Export the class
window.TTNGVisualizer = TTNGVisualizer; 