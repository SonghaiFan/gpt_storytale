class TTNGVisualizer {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = d3.select(`#${this.containerId}`);
        this.nodeRadius = 30;
        this.colors = {
            node: {
                empty: '#f8f9fa',
                filled: '#69b3a2',
                stroke: '#e9ecef'
            },
            track: {
                background: '#f8f9fa',
                border: '#e9ecef'
            },
            link: '#aaa',
            text: '#495057',
            axis: '#adb5bd'
        };
        
        // Layout settings
        this.layout = {
            padding: {
                top: 80,    // Space for time labels
                right: 60,
                bottom: 40,
                left: 120   // Space for track labels
            },
            track: {
                height: 100,     // Total height of track container
                spacing: 20,     // Space between tracks
            },
            time: {
                width: 220,      // Width between timepoints
                labelOffset: 40  // Vertical offset for time labels
            }
        };
        
        // Initialize
        this.initializeSVG();
        
        // Handle window resize
        window.addEventListener('resize', this.resize.bind(this));
    }
    
    initializeSVG() {
        // Clear any existing SVG
        this.container.selectAll("*").remove();
        
        // Create responsive SVG
        this.svg = this.container.append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .style('min-height', '400px');
            
        // Add zoom behavior
        this.g = this.svg.append('g');
        this.zoom = d3.zoom()
            .scaleExtent([0.5, 2])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });
            
        this.svg.call(this.zoom);
            
        // Add arrow marker for links
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', this.nodeRadius + 9)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('xoverflow', 'visible')
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', this.colors.link)
            .style('stroke', 'none');
            
        // Get container dimensions
        this.updateDimensions();
    }
    
    updateDimensions() {
        const rect = this.container.node().getBoundingClientRect();
        this.width = rect.width;
        this.height = rect.height;
        
        this.svg
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .attr('preserveAspectRatio', 'xMidYMid meet');
    }
    
    resize() {
        this.updateDimensions();
        if (this.currentData) {
            this.visualize(this.currentData);
        }
    }
    
    initializeGrid(numTracks, numTimepoints) {
        const gridNodes = [];
        
        // Create grid nodes
        for (let track = 1; track <= numTracks; track++) {
            for (let timepoint = 1; timepoint <= numTimepoints; timepoint++) {
                gridNodes.push({
                    id: `t${timepoint}_track${track}`,
                    track: track,
                    timepoint: timepoint,
                    isEmpty: true
                });
            }
        }
        
        this.visualize({ nodes: gridNodes, edges: [] });
    }
    
    visualize(data) {
        this.currentData = data;
        
        // Clear previous visualization
        this.g.selectAll('*').remove();
        
        if (!data.nodes || data.nodes.length === 0) return;
        
        const numTracks = Math.max(...data.nodes.map(n => n.track));
        const numTimepoints = Math.max(...data.nodes.map(n => n.timepoint));
        
        // Calculate dimensions
        const totalWidth = (numTimepoints - 1) * this.layout.time.width;
        const totalHeight = numTracks * (this.layout.track.height + this.layout.track.spacing);
        
        // Calculate starting positions to center the graph
        const startX = (this.width - totalWidth) / 2;
        const startY = (this.height - totalHeight) / 2;
        
        // Create track backgrounds
        const tracks = this.g.append('g')
            .attr('class', 'tracks')
            .selectAll('rect')
            .data(d3.range(1, numTracks + 1))
            .join('rect')
            .attr('x', startX - this.layout.padding.left / 2)
            .attr('y', d => startY + (d - 1) * (this.layout.track.height + this.layout.track.spacing))
            .attr('width', totalWidth + this.layout.padding.left + this.layout.padding.right)
            .attr('height', this.layout.track.height)
            .attr('rx', this.layout.track.height / 2)  // Make fully rounded by setting radius to half height
            .attr('ry', this.layout.track.height / 2)
            .attr('fill', this.colors.track.background)
            .attr('stroke', this.colors.track.border)
            .attr('stroke-width', 1);
            
        // Create time axis
        const timeAxis = this.g.append('g')
            .attr('class', 'time-axis');
            
        // Time labels
        timeAxis.selectAll('text')
            .data(d3.range(1, numTimepoints + 1))
            .join('text')
            .attr('x', d => startX + (d - 1) * this.layout.time.width)
            .attr('y', startY - this.layout.time.labelOffset)
            .attr('text-anchor', 'middle')
            .attr('fill', this.colors.axis)
            .text(d => `T${d}`);
            
        // Track labels
        const trackLabels = this.g.append('g')
            .attr('class', 'track-labels')
            .selectAll('text')
            .data(d3.range(1, numTracks + 1))
            .join('text')
            .attr('x', startX - this.layout.padding.left * 0.6)
            .attr('y', d => startY + (d - 1) * (this.layout.track.height + this.layout.track.spacing) + this.layout.track.height / 2)
            .attr('text-anchor', 'end')
            .attr('dominant-baseline', 'middle')
            .attr('fill', this.colors.axis)
            .text(d => `Track ${d}`);
        
        // Create the links
        const links = this.g.append('g')
            .attr('class', 'links')
            .selectAll('path')
            .data(data.edges)
            .join('path')
            .attr('class', 'link')
            .attr('stroke', this.colors.link)
            .attr('stroke-width', 2)
            .attr('fill', 'none')
            .attr('marker-end', 'url(#arrowhead)')
            .attr('d', d => {
                const source = data.nodes.find(n => n.id === (d.from || d.source));
                const target = data.nodes.find(n => n.id === (d.to || d.target));
                if (!source || !target) return '';
                
                const sourceX = startX + (source.timepoint - 1) * this.layout.time.width;
                const sourceY = startY + (source.track - 1) * (this.layout.track.height + this.layout.track.spacing) + this.layout.track.height / 2;
                const targetX = startX + (target.timepoint - 1) * this.layout.time.width;
                const targetY = startY + (target.track - 1) * (this.layout.track.height + this.layout.track.spacing) + this.layout.track.height / 2;
                
                return `M${sourceX},${sourceY}L${targetX},${targetY}`;
            });
            
        // Create the nodes
        const nodes = this.g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(data.nodes)
            .join('g')
            .attr('class', 'node')
            .attr('transform', d => {
                const x = startX + (d.timepoint - 1) * this.layout.time.width;
                const y = startY + (d.track - 1) * (this.layout.track.height + this.layout.track.spacing) + this.layout.track.height / 2;
                return `translate(${x},${y})`;
            })
            .on('mouseenter', (event, d) => {
                const node = d3.select(event.currentTarget);
                node.raise();
                node.classed('node-highlight', true);
            })
            .on('mouseleave', (event, d) => {
                const node = d3.select(event.currentTarget);
                node.classed('node-highlight', false);
            });
                
        // Add circles for nodes
        nodes.append('circle')
            .attr('r', this.nodeRadius)
            .attr('fill', d => d.isEmpty ? this.colors.node.empty : this.colors.node.filled)
            .attr('stroke', this.colors.node.stroke)
            .attr('stroke-width', d => d.isEmpty ? 1.5 : 2);
            
        // Add attributes if node is not empty
        nodes.filter(d => !d.isEmpty).each((d, i, nodes) => {
            const node = d3.select(nodes[i]);
            const attributeLabels = node.append('g')
                .attr('class', 'attributes');
                
            if (d.attributes?.topics?.[0]) {
                attributeLabels.append('text')
                    .attr('y', -5)
                    .attr('text-anchor', 'middle')
                    .attr('fill', this.colors.text)
                    .text(d.attributes.topics[0]);
            }
            
            if (d.attributes?.entities?.[0]) {
                attributeLabels.append('text')
                    .attr('y', 15)
                    .attr('text-anchor', 'middle')
                    .attr('fill', this.colors.text)
                    .text(d.attributes.entities[0]);
            }
        });
        
        // Center and fit the visualization
        this.centerAndFitGraph(startX, startY, totalWidth, totalHeight);
    }
    
    centerAndFitGraph(startX, startY, totalWidth, totalHeight) {
        const padding = 50;
        const scale = Math.min(
            (this.width - padding * 2) / (totalWidth + this.layout.padding.left + this.layout.padding.right),
            (this.height - padding * 2) / (totalHeight + this.layout.padding.top + this.layout.padding.bottom)
        );
        
        const transform = d3.zoomIdentity
            .translate(this.width / 2, this.height / 2)
            .scale(Math.min(scale, 1))  // Don't scale up beyond 1
            .translate(
                -(startX + totalWidth / 2),
                -(startY + totalHeight / 2)
            );
            
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, transform);
    }
    
    updateNode(nodeId, attributes) {
        if (!this.currentData) return;
        
        const nodeIndex = this.currentData.nodes.findIndex(n => n.id === nodeId);
        if (nodeIndex === -1) return;
        
        this.currentData.nodes[nodeIndex] = {
            ...this.currentData.nodes[nodeIndex],
            isEmpty: false,
            attributes
        };
        
        this.visualize(this.currentData);
    }
    
    addEdge(sourceId, targetId) {
        if (!this.currentData) return;
        
        this.currentData.edges.push({
            source: sourceId,
            target: targetId
        });
        
        this.visualize(this.currentData);
    }
    
    removeEdge(sourceId, targetId) {
        if (!this.currentData) return;
        
        this.currentData.edges = this.currentData.edges.filter(
            e => !(e.source === sourceId && e.target === targetId)
        );
        
        this.visualize(this.currentData);
    }
}

// Export the class
window.TTNGVisualizer = TTNGVisualizer; 