document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const findPathBtn = document.getElementById('findPathBtn');
    const sendSMSBtn = document.getElementById('sendSMSBtn');
    const startLocation = document.getElementById('startLocation');
    const endLocation = document.getElementById('endLocation');
    const pathResult = document.getElementById('pathResult');
    const pathSummary = document.getElementById('pathSummary');
    const pathDetails = document.getElementById('pathDetails');
    const pathTimeDistance = document.getElementById('pathTimeDistance');
    const campusMap = document.getElementById('campusMap');
    const mapContainer = document.querySelector('.map-container');
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    let campusGraph = window.graphData || {};
    // Create canvas overlay
    const canvas = document.createElement('canvas');
    canvas.id = 'pathCanvas';
    Object.assign(canvas.style, {
        position: 'absolute',
        top: '0',
        left: '0',
        pointerEvents: 'none'
    });
    mapContainer.style.position = 'relative';
    mapContainer.appendChild(canvas);
    
    // State
    // let currentPath = null;
    // let campusGraph = {}; // Will be populated from backend
    
    // Initialize the application
    async function init() {
        // Initialize with the graph data passed from Flask
        campusGraph = window.graphData || {};
        setupEventListeners();
        await loadLocations();
        resizeCanvas();
    }
    
    // Load locations from backend
    async function loadLocations() {
        try {
            loadingIndicator.style.display = 'block';
            const response = await fetch('/get_locations');
            if (!response.ok) throw new Error('Failed to load locations');
            
            const data = await response.json();
            populateLocationDropdowns(data.locations);
            
            // Load graph data from template (passed from Flask)
            campusGraph = window.graphData || {};
        } catch (error) {
            showNotification(`Error: ${error.message}`, 'error');
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }
    
    // Populate dropdowns with locations
    function populateLocationDropdowns(locations) {
        startLocation.innerHTML = '<option value="">Select starting point</option>';
        endLocation.innerHTML = '<option value="">Select destination</option>';
        
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location.id;
            option.textContent = location.name;
            
            startLocation.appendChild(option.cloneNode(true));
            endLocation.appendChild(option);
        });
    }
    
    // Setup event listeners
    function setupEventListeners() {
        campusMap.onload = resizeCanvas;
        window.addEventListener('resize', resizeCanvas);
        
        findPathBtn.addEventListener('click', handleFindPath);
        sendSMSBtn.addEventListener('click', handleSendSMS);
    }
    
    // Resize canvas to match image
    function resizeCanvas() {
        canvas.width = campusMap.offsetWidth;
        canvas.height = campusMap.offsetHeight;
        if (currentPath) {
            drawPath(currentPath.path.coordinates);
        }
    }
    
    // Find path button handler
    async function handleFindPath() {
        const startId = parseInt(startLocation.value);
        const endId = parseInt(endLocation.value);
        
        if (!startId || !endId) {
            showNotification('Please select both starting point and destination', 'warning');
            return;
        }
        
        try {
            setLoading(findPathBtn, true);
            
            const response = await fetch('/get_path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start: startId,
                    end: endId
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to find path');
            }
            
            const data = await response.json();
            currentPath = data;
            
            displayPath(data);
            drawPath(data.path.coordinates);
            sendSMSBtn.disabled = false;
            pathResult.classList.remove('hidden');
        } catch (error) {
            console.error('Pathfinding Error:', error);
            showNotification(`Failed to find path: ${error.message}`, 'error');
        } finally {
            setLoading(findPathBtn, false);
        }
    }
    
    // Send SMS button handler
    async function handleSendSMS() {
    const phoneNumber = prompt('Please enter your phone number with country code (e.g., +91...):');
    if (!phoneNumber) return;
    
    try {
        setLoading(sendSMSBtn, true);
        
        // Prepare path data with proper node references
        const smsPathData = {
            start: {
                node_id: currentPath.path.nodes[0],
                name: currentPath.path.start.name
            },
            end: {
                node_id: currentPath.path.nodes[currentPath.path.nodes.length - 1],
                name: currentPath.path.end.name
            },
            path_details: currentPath.path.coordinates.map(coord => {
                if (coord.type === 'path') {
                    return {
                        from_node: coord.from_node,
                        to_node: coord.to_node,
                        path_type: coord.path_type,
                        type: 'path'
                    };
                }
                return coord;
            }),
            estimated_time: currentPath.path.estimated_time
        };

        const response = await fetch('/send_sms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone: phoneNumber,
                path: smsPathData
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to send SMS');
        }
        
        const data = await response.json();
        showNotification(`SMS sent successfully to ${phoneNumber}\n\nPreview:\n${data.preview}`);
    } catch (error) {
        console.error('SMS Error:', error);
        showNotification(`Failed to send SMS: ${error.message}\n\nPlease check the phone number format and try again.`, 'error');
    } finally {
        setLoading(sendSMSBtn, false);
    }
}
    
    // Display path information
    function displayPath(pathData) {
        if (!pathData?.path) {
            showNotification('Invalid path data received', 'error');
            return;
        }
    
        // Display summary with actual names
        const startName = pathData.path.start?.name || `Location ${pathData.path.nodes[0]}`;
        const endName = pathData.path.end?.name || `Location ${pathData.path.nodes.slice(-1)[0]}`;
        pathSummary.innerHTML = `📍 <strong>Route from ${startName} to ${endName}</strong>`;
        
        // Display time estimate
        pathTimeDistance.innerHTML = `⏱️ <strong>${pathData.path.estimated_time || 'N/A'}</strong> estimated walk time`;
    
        // Display detailed steps
        pathDetails.innerHTML = '';
        let stepCount = 1;
    
        // Group coordinates into segments
        const segments = [];
        let currentSegment = null;
    
        pathData.path.coordinates.forEach((point, index) => {
            if (!point) return;
    
            if (point.type === 'node') {
                if (currentSegment) {
                    segments.push(currentSegment);
                    currentSegment = null;
                }
            } else if (point.type === 'path') {
                if (!currentSegment) {
                    currentSegment = {
                        from_node: point.from_node,
                        to_node: point.to_node,
                        path_type: point.path_type,
                        points: []
                    };
                }
                currentSegment.points.push(point);
            }
        });
    
        // Display each segment with emoji and actual names
        segments.forEach(segment => {
            // Get actual names from the path data or graph data
            const fromName = pathData.path.coordinates.find(p => 
                p.type === 'node' && p.node_id === segment.from_node
            )?.name || campusGraph.nodes?.[segment.from_node]?.name || `Location ${segment.from_node}`;
            
            const toName = pathData.path.coordinates.find(p => 
                p.type === 'node' && p.node_id === segment.to_node
            )?.name || campusGraph.nodes?.[segment.to_node]?.name || `Location ${segment.to_node}`;
    
            const segmentDiv = document.createElement('div');
            segmentDiv.className = 'path-segment mb-3';
    
            // Get emoji based on path type
            let emoji = '🚶';
            let pathDesc = segment.path_type.replace('_', ' ');
            
            switch(segment.path_type) {
                case 'stairs':
                    emoji = '🪜';
                    pathDesc = 'stairs';
                    break;
                case 'food_court':
                    emoji = '🍔';
                    pathDesc = 'food court area';
                    break;
                case 'crowded_area':
                    emoji = '👥';
                    pathDesc = 'crowded area';
                    break;
                case 'open_path':
                    emoji = '🌳';
                    pathDesc = 'open path';
                    break;
            }
    
            segmentDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="step-number me-2">${stepCount++}.</div>
                    <div>
                        <strong>${emoji} ${fromName} → ${toName}</strong>
                        <div class="text-muted">Via ${pathDesc}</div>
                    </div>
                </div>
            `;
            
            pathDetails.appendChild(segmentDiv);
        });
    
        // Add start and end markers with actual names
        if (pathData.path.coordinates.length > 0) {
            const firstNode = pathData.path.coordinates[0];
            const lastNode = pathData.path.coordinates[pathData.path.coordinates.length - 1];
            
            if (firstNode?.type === 'node') {
                const startDiv = document.createElement('div');
                startDiv.className = 'path-start mb-3 p-2 bg-light rounded';
                const startName = firstNode.name || campusGraph.nodes?.[firstNode.node_id]?.name || `Location ${firstNode.node_id}`;
                startDiv.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="me-2">🚦</div>
                        <div><strong>Start:</strong> ${startName}</div>
                    </div>
                `;
                pathDetails.insertBefore(startDiv, pathDetails.firstChild);
            }
            
            if (lastNode?.type === 'node') {
                const endDiv = document.createElement('div');
                endDiv.className = 'path-end mt-3 p-2 bg-light rounded';
                const endName = lastNode.name || campusGraph.nodes?.[lastNode.node_id]?.name || `Location ${lastNode.node_id}`;
                endDiv.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="me-2">🏁</div>
                        <div><strong>Destination:</strong> ${endName}</div>
                    </div>
                `;
                pathDetails.appendChild(endDiv);
            }
        }
    }
    
    // Draw path on the map
    
    function setLoading(button, isLoading) {
        
    }
    
    // Improved notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 500);
        }, 3000);
    }
    
    // Initialize
    init();
});