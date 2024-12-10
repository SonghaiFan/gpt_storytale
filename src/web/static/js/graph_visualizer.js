class TTNGVisualizer {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = this.container.node().getBoundingClientRect().height;
        this.margin = { top: 60, right: 40, bottom: 60, left: 80 };
        this.nodeRadius = 20;  // Define node radius as a class property
        
        this.svg = this.container.append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, this.width, this.height]);
        
        // Create a group for zoomable content
        this.zoomGroup = this.svg.append('g').attr('class', 'zoom-group');
        
        // Add layers in correct order
        this.trackGroup = this.zoomGroup.append('g').attr('class', 'tracks');
        this.edgeGroup = this.zoomGroup.append('g').attr('class', 'edges');
        this.nodeGroup = this.zoomGroup.append('g').attr('class', 'nodes');
        
        // Axes groups (outside zoom group)
        this.xAxisGroup = this.svg.append('g').attr('class', 'x-axis');
        this.yAxisGroup = this.svg.append('g').attr('class', 'y-axis');
        
        this.nodes = new Map();
        this.edges = new Set();
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.5, 2])
            .on('zoom', (event) => this._handleZoom(event));
        
        this.svg.call(zoom);
    }
    
    _handleZoom(event) {
        const transform = event.transform;
        
        // Transform the main content
        this.zoomGroup.attr('transform', transform);
        
        // Update axes
        if (this.xScale && this.yScale) {
            // Create new scaled axes
            const newXScale = transform.rescaleX(this.xScale);
            const newYScale = transform.rescaleY(this.yScale);
            
            // Update axes with new scales
            this.xAxisGroup.call(this.xAxis.scale(newXScale));
            this.yAxisGroup.call(this.yAxis.scale(newYScale));
        }
    }
    
    initializeGrid(numTracks, numTimepoints, nodes) {
        this.clear();
        
        const contentWidth = this.width - this.margin.left - this.margin.right;
        const contentHeight = this.height - this.margin.top - this.margin.bottom;
        
        // Calculate track dimensions
        const nodeSpacing = 20;  // Space between node and track edge
        const trackHeight = this.nodeRadius * 2 + nodeSpacing * 2;  // Height to wrap node with padding
        const trackPadding = 40;  // Space between tracks
        
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
            .tickFormat(d => Number.isInteger(d) ? `T${d}` : '')
            .tickSize(-contentHeight);
            
        this.yAxis = d3.axisLeft(this.yScale)
            .ticks(numTracks)
            .tickFormat(d => Number.isInteger(d) ? `Track ${d}` : '')
            .tickSize(-contentWidth);
        
        // Add axes
        this.xAxisGroup
            .attr('transform', `translate(0,${this.margin.top})`)
            .call(this.xAxis);
        
        this.yAxisGroup
            .attr('transform', `translate(${this.margin.left},0)`)
            .call(this.yAxis);
        
        // Draw tracks
        for (let track = 1; track <= numTracks; track++) {
            const y = this.yScale(track);
            
            // Draw track background
            this.trackGroup.append('rect')
                .attr('class', 'track-bg')
                .attr('x', this.margin.left + nodeSpacing)  // Add padding from left
                .attr('y', y - trackHeight/2)  // Center around track position
                .attr('width', contentWidth - nodeSpacing * 2)  // Subtract padding from both sides
                .attr('height', trackHeight)
                .attr('rx', trackHeight/2)  // Make corners fully rounded
                .attr('ry', trackHeight/2)
                .attr('fill', '#f8f9fa')
                .attr('stroke', '#e9ecef');
            
            // Add nodes for this track
            for (let timepoint = 1; timepoint <= numTimepoints; timepoint++) {
                const x = this.xScale(timepoint);
                const nodeId = `t${timepoint}_track${track}`;
                const nodeData = nodes.get(nodeId);
                
                this.nodes.set(nodeId, { x, y, ...nodeData });
            }
        }
        
        this._updateVisualization();
    }
    
    clear() {
        this.nodes.clear();
        this.edges.clear();
        this.trackGroup.selectAll('*').remove();
        this.edgeGroup.selectAll('*').remove();
        this.nodeGroup.selectAll('*').remove();
        this.xAxisGroup.selectAll('*').remove();
        this.yAxisGroup.selectAll('*').remove();
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
    
    _updateVisualization() {
        // Update edges
        const edgeElements = this.edgeGroup
            .selectAll('path')
            .data(Array.from(this.edges), d => d);
        
        edgeElements.exit().remove();
        
        const edgeEnter = edgeElements.enter()
            .append('path')
            .attr('class', 'edge')
            .attr('stroke', '#adb5bd')
            .attr('stroke-width', 2)
            .attr('fill', 'none')
            .attr('marker-end', 'url(#arrow)');
        
        edgeElements.merge(edgeEnter)
            .attr('d', edge => {
                const [fromId, toId] = edge.split('->');
                const source = this.nodes.get(fromId);
                const target = this.nodes.get(toId);
                return `M${source.x},${source.y} L${target.x},${target.y}`;
            });
        
        // Update nodes
        const nodeElements = this.nodeGroup
            .selectAll('.node')
            .data(Array.from(this.nodes.entries()), d => d[0]);
        
        nodeElements.exit().remove();
        
        const nodeEnter = nodeElements.enter()
            .append('g')
            .attr('class', 'node')
            .attr('data-node-id', d => d[0]);
        
        nodeEnter.append('circle')
            .attr('r', this.nodeRadius);  // Use class property for consistency
        
        const allNodes = nodeElements.merge(nodeEnter)
            .attr('transform', d => `translate(${d[1].x},${d[1].y})`);
        
        allNodes.select('circle')
            .attr('class', d => d[1].isEmpty ? 'node-empty' : '')
            .attr('fill', d => d[1].isEmpty ? '#fff' : '#4dabf7')
            .attr('stroke', '#1c7ed6')
            .attr('stroke-width', 2);
    }
}

// Export the class
window.TTNGVisualizer = TTNGVisualizer; 