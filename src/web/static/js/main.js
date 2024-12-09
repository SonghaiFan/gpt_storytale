document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const loadingDiv = document.getElementById('loading');
    const storyOutput = document.getElementById('story-output');
    const storyGrid = document.getElementById('story-grid');

    generateBtn.addEventListener('click', async () => {
        const numTracks = document.getElementById('num-tracks').value;
        const numTimepoints = document.getElementById('num-timepoints').value;
        const organizingAttribute = document.getElementById('organizing-attribute').value;
        const graphGenre = document.getElementById('graph-genre').value;
        
        // Get custom attributes
        const customEntities = document.getElementById('custom-entities').value
            .split(',')
            .map(item => item.trim())
            .filter(item => item.length > 0);
        
        const customEvents = document.getElementById('custom-events').value
            .split(',')
            .map(item => item.trim())
            .filter(item => item.length > 0);
        
        const customTopics = document.getElementById('custom-topics').value
            .split(',')
            .map(item => item.trim())
            .filter(item => item.length > 0);

        // Get story style preferences
        const cefrLevel = document.getElementById('cefr-level').value;
        const tone = document.getElementById('tone').value;

        // Show loading state
        loadingDiv.classList.remove('hidden');
        storyOutput.classList.add('hidden');
        generateBtn.disabled = true;
        generateBtn.classList.add('opacity-50');

        try {
            const response = await fetch('/generate_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    num_tracks: numTracks,
                    num_timepoints: numTimepoints,
                    organizing_attribute: organizingAttribute,
                    graph_genre: graphGenre,
                    custom_attributes: {
                        entities: customEntities,
                        events: customEvents,
                        topics: customTopics
                    },
                    style: {
                        cefr_level: cefrLevel,
                        tone: tone
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                displayStory(data.story);
            } else {
                alert('Error generating story: ' + data.error);
            }
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            loadingDiv.classList.add('hidden');
            generateBtn.disabled = false;
            generateBtn.classList.remove('opacity-50');
        }
    });

    function displayStory(story) {
        storyGrid.innerHTML = '';
        const tracks = {};

        // Group nodes by track
        story.nodes.forEach(node => {
            if (!tracks[node.track]) {
                tracks[node.track] = [];
            }
            tracks[node.track].push(node);
        });

        // Sort nodes within each track by timepoint
        Object.values(tracks).forEach(trackNodes => {
            trackNodes.sort((a, b) => a.timepoint - b.timepoint);
        });

        // Create track containers
        Object.entries(tracks).forEach(([trackNum, nodes]) => {
            const trackDiv = document.createElement('div');
            trackDiv.className = 'story-track fade-in';
            
            const trackTitle = document.createElement('h3');
            trackTitle.className = 'story-track-title';
            trackTitle.textContent = `Track ${trackNum}`;
            trackDiv.appendChild(trackTitle);

            nodes.forEach(node => {
                const nodeDiv = document.createElement('div');
                nodeDiv.className = 'story-node';

                // Create the main content
                const contentDiv = document.createElement('div');
                contentDiv.className = 'story-node-content';
                contentDiv.textContent = node.text;

                // Create attributes section if available
                let attributesHtml = '';
                if (node.attributes) {
                    attributesHtml = `
                        <div class="story-node-attributes">
                            <div class="attribute-item">
                                <span class="attribute-label">Topics:</span> 
                                ${node.attributes.topics.join(', ')}
                            </div>
                            <div class="attribute-item">
                                <span class="attribute-label">Entities:</span> 
                                ${node.attributes.entities.join(', ')}
                            </div>
                            <div class="attribute-item">
                                <span class="attribute-label">Events:</span> 
                                ${node.attributes.events.join(', ')}
                            </div>
                        </div>
                    `;
                }

                // Create the time indicator
                const timeDiv = document.createElement('div');
                timeDiv.className = 'story-node-time';
                timeDiv.textContent = `Timepoint ${node.timepoint}`;

                // Combine all elements
                nodeDiv.innerHTML = `
                    ${contentDiv.outerHTML}
                    ${attributesHtml}
                    ${timeDiv.outerHTML}
                `;

                trackDiv.appendChild(nodeDiv);
            });

            storyGrid.appendChild(trackDiv);
        });

        // Display save information if available
        if (story.saved_file) {
            const saveInfo = document.createElement('div');
            saveInfo.className = 'save-info fade-in mt-4 text-sm text-gray-600';
            saveInfo.textContent = `Story saved as: ${story.saved_file}`;
            storyGrid.appendChild(saveInfo);
        }

        storyOutput.classList.remove('hidden');
    }
}); 