const API_BASE = `${window.location.protocol}//${window.location.host}`;
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
let currentSessionId = null;
let currentVncPort = null;
let currentDisplayNum = null;
let currentTaskId = null;
let taskPollingInterval = null;
let taskWebSocket = null;
let tabSessionId = `tab-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// ====================================================================
// Display Management - Multi-monitor support (2 displays: ports 6080, 6081)
// ====================================================================

function displayNumFromPort(port) {
    return port ? port - 6079 : 1; // 6080 -> 1, 6081 -> 2
}

function setVncDisplay(port, viewOnly = true) {
    if (!port) return;
    currentVncPort = port;
    currentDisplayNum = displayNumFromPort(port);
    const vncFrame = document.getElementById('vncFrame');
    const vncPlaceholder = document.getElementById('vncPlaceholder');
    
    const vncUrl = `http://localhost:${port}/vnc.html?path=websockify&resize=scale&autoconnect=1&reconnect=1&reconnect_delay=2000&view_only=${viewOnly ? 1 : 0}`;
    vncFrame.src = vncUrl;
    
    // Hide placeholder and show VNC iframe
    if (vncPlaceholder) vncPlaceholder.style.display = 'none';
    vncFrame.style.display = 'block';
    
    addMessage(`Using Display ${currentDisplayNum} (VNC port ${port})`, 'system');
}

function showVncPlaceholder() {
    const vncFrame = document.getElementById('vncFrame');
    const vncPlaceholder = document.getElementById('vncPlaceholder');
    
    if (vncFrame) vncFrame.style.display = 'none';
    if (vncPlaceholder) vncPlaceholder.style.display = 'flex';
}

function initializeVNCDisplay() {
    // Show placeholder on page load if no session
    if (!currentVncPort) {
        showVncPlaceholder();
    }
}

// Clean up display assignment when tab closes
window.addEventListener('beforeunload', () => {
    let activeDisplays = JSON.parse(localStorage.getItem('activeDisplays') || '{}');
    delete activeDisplays[tabSessionId];
    localStorage.setItem('activeDisplays', JSON.stringify(activeDisplays));
    
    if (taskPollingInterval) clearInterval(taskPollingInterval);
    if (taskWebSocket) taskWebSocket.close();
});

// ====================================================================
// Utility Functions
// ====================================================================

function showLoadingModal() {
    const modal = document.getElementById('loadingModal');
    if (modal) {
        modal.classList.add('active');
    }
}

function hideLoadingModal() {
    const modal = document.getElementById('loadingModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function apiCall(method, endpoint, data = null) {
    try {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function addMessage(text, type = 'system', time = new Date()) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    
    // Handle screenshot type - render as image
    if (type === 'screenshot') {
        const imgEl = document.createElement('img');
        imgEl.src = `data:image/png;base64,${text}`;
        imgEl.style.maxWidth = '100%';
        imgEl.style.borderRadius = '4px';
        imgEl.style.marginTop = '8px';
        messageEl.appendChild(imgEl);
    } else {
        const textEl = document.createElement('div');
        // Render markdown for assistant messages, plain text for others
        if (type === 'assistant' && typeof marked !== 'undefined') {
            textEl.innerHTML = marked.parse(text);
        } else {
            textEl.textContent = text;
        }
        messageEl.appendChild(textEl);
    }
    
    if (type !== 'system') {
        const timeEl = document.createElement('div');
        timeEl.className = 'message-time';
        timeEl.textContent = time.toLocaleTimeString();
        messageEl.appendChild(timeEl);
    }
    
    messagesDiv.appendChild(messageEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateSessionInfo(text) {
    document.getElementById('session-info').textContent = text;
}

// ====================================================================
// Session Management
// ====================================================================

async function createNewSession() {
    try {
        // Show loading modal
        showLoadingModal();
        
        // Clear previous chat messages IMMEDIATELY
        const chatDiv = document.getElementById('chatMessages');
        chatDiv.innerHTML = '';
        
        const session = await apiCall('POST', '/sessions', {
            provider: 'anthropic',
            model: 'claude-sonnet-4-5-20250929'
        });
        
        currentSessionId = session.id;
        currentTaskId = null;
        currentVncPort = session.vnc_port;
        currentDisplayNum = displayNumFromPort(session.vnc_port);
        updateSessionInfo(`Session: ${session.id.substring(0, 8)}...`);
        addMessage(`Session created successfully`, 'system');
        setVncDisplay(session.vnc_port, true);
        
        // Refresh session list to show new session
        await listSessions();
        
        return session;
    } catch (error) {
        addMessage(`Failed to create session: ${error.message}`, 'system');
    } finally {
        // Hide loading modal on success or error
        hideLoadingModal();
    }
}

async function startSession() {
    if (!currentSessionId) {
        addMessage('No session available to start', 'system');
        return;
    }
    
    try {
        await apiCall('POST', `/sessions/${currentSessionId}/start`, {});
        addMessage('Session started and ready', 'system');
    } catch (error) {
        addMessage(`Failed to start session: ${error.message}`, 'system');
    }
}

async function listSessions() {
    try {
        const data = await apiCall('GET', '/sessions');
        const sessionList = document.getElementById('sessionList');
        
        if (!data.sessions || data.sessions.length === 0) {
            sessionList.innerHTML = '<div style="padding: 20px; text-align: center; color: #999; font-size: 12px;">No sessions available</div>';
            return;
        }
        
        sessionList.innerHTML = '';
        data.sessions.forEach(session => {
            const sessionEl = document.createElement('div');
            sessionEl.className = `session-item ${session.id === currentSessionId ? 'active' : ''}`;
            sessionEl.innerHTML = `
                <div class="session-id">${session.id.substring(0, 8)}...</div>
                <div class="session-model">${session.model || 'Unknown Model'}</div>
            `;
            sessionEl.onclick = () => selectSession(session);
            sessionList.appendChild(sessionEl);
        });
    } catch (error) {
        console.error('Failed to list sessions:', error);
    }
}

async function selectSession(session) {
    currentSessionId = session.id;
    currentTaskId = null;
    currentVncPort = session.vnc_port;
    currentDisplayNum = displayNumFromPort(session.vnc_port);
    
    // Close any active WebSocket connection
    if (taskWebSocket && taskWebSocket.readyState === WebSocket.OPEN) {
        taskWebSocket.close();
    }
    
    // Clear any pending polling intervals
    if (taskPollingInterval) {
        clearInterval(taskPollingInterval);
        taskPollingInterval = null;
    }
    
    // Clear chat messages
    const chatDiv = document.getElementById('chatMessages');
    chatDiv.innerHTML = '';
    
    updateSessionInfo(`Session: ${session.id.substring(0, 8)}...`);
    addMessage(`Switched to session: ${session.id.substring(0, 8)}...`, 'system');
    setVncDisplay(session.vnc_port, true);
    
    // Load tasks for this session
    await loadSessionTasks();
    
    // Refresh the session list to highlight active session
    await listSessions();
}

function refreshSessions() {
    addMessage('Refreshing sessions...', 'system');
    listSessions();
}

// ====================================================================
// Task Management
// ====================================================================

async function startNewTask() {
    const taskInput = document.getElementById('newTaskInput');
    const description = taskInput.value.trim();
    
    if (!description) {
        addMessage('Please enter a task description', 'system');
        return;
    }
    
    if (!currentSessionId) {
        addMessage('Please create a session first by clicking "New Agent Task" in the Sessions panel', 'system');
        return;
    }
    
    // Clear input after validation
    taskInput.value = '';
    
    try {
        addMessage(description, 'user');
        
        const displayNum = currentDisplayNum || 1;
        const task = await apiCall('POST', `/sessions/${currentSessionId}/tasks`, {
            description: description,
            max_iterations: 10,
            display_num: displayNum
        });
        
        currentTaskId = task.id;
        
        addMessage('Task started...', 'system');
        //addTaskToHistory(task);
        
        // Start polling for task updates
        startTaskPolling();
        
    } catch (error) {
        addMessage(`Failed to start task: ${error.message}`, 'system');
    }
}

function addTaskToHistory(task) {
    const historyDiv = document.getElementById('taskHistory');
    
    // Clear placeholder
    if (historyDiv.querySelector('div[style*="No tasks"]')) {
        historyDiv.innerHTML = '';
    }
    
    const taskItem = document.createElement('div');
    taskItem.className = 'task-item active';
    taskItem.id = `task-${task.id}`;
    taskItem.onclick = () => selectTask(task.id);
    
    taskItem.innerHTML = `
        <div class="task-status">${task.status}</div>
        <div class="task-desc">${task.description}</div>
        <div class="task-time">${new Date(task.created_at).toLocaleTimeString()}</div>
    `;
    
    historyDiv.insertBefore(taskItem, historyDiv.firstChild);
}

async function loadSessionTasks() {
    if (!currentSessionId) return;
    
    try {
        console.log('Loading tasks for session:', currentSessionId);
        const data = await apiCall('GET', `/sessions/${currentSessionId}/tasks`);
        const historyDiv = document.getElementById('taskHistory');
        historyDiv.innerHTML = '';
        
        if (!data.tasks || data.tasks.length === 0) {
            historyDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #999; font-size: 12px;">No tasks yet</div>';
            return;
        }
        
        data.tasks.forEach(task => {
            addTaskToHistory(task);
        });
        
    } catch (error) {
        console.error('Failed to load tasks:', error);
    }
}

function selectTask(taskId) {
    currentTaskId = taskId;
    
    // Update UI
    document.querySelectorAll('.task-item').forEach(el => {
        el.classList.remove('active');
    });
    document.getElementById(`task-${taskId}`)?.classList.add('active');
    
    // Load task details
    loadTaskDetails(taskId);
}

async function loadTaskDetails(taskId) {
    try {
        const task = await apiCall('GET', `/tasks/${taskId}`);
        
        // Clear and repopulate messages
        const messagesDiv = document.getElementById('chatMessages');
        messagesDiv.innerHTML = '';
        
        addMessage(`Task: ${task.description}`, 'user');
        
        if (task.messages && task.messages.length > 0) {
            task.messages.forEach(msg => {
                if (msg.role === 'assistant') {
                    if (msg.content) {
                        msg.content.forEach(block => {
                            if (block.type === 'text') {
                                addMessage(block.text, 'assistant');
                            } else if (block.type === 'tool_use') {
                                addMessage(`Tool: ${block.name}\nAction: ${JSON.stringify(block.input, null, 2)}`, 'tool-use');
                            }
                        });
                    }
                }
            });
        }
        
        // Update task status in history
        const taskItem = document.getElementById(`task-${taskId}`);
        if (taskItem) {
            taskItem.querySelector('.task-status').textContent = task.status;
        }
        
        if (task.status === 'running') {
            document.getElementById('taskStatusIndicator').innerHTML = '<span class="loading"></span>';
        } else {
            document.getElementById('taskStatusIndicator').textContent = '';
        }
        
    } catch (error) {
        console.error('Failed to load task details:', error);
    }
}

function startTaskPolling() {
    if (currentTaskId) {
        connectTaskWebSocket(currentTaskId);
    }
}

function connectTaskWebSocket(taskId) {
    // Close existing connection
    if (taskWebSocket) {
        taskWebSocket.close();
    }
    
    const wsUrl = `${WS_BASE}/ws/tasks/${taskId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    taskWebSocket = new WebSocket(wsUrl);
    
    taskWebSocket.onopen = () => {
        console.log('WebSocket connected for task updates');
        //addMessage('Connected to task updates', 'system');
    };
    
    taskWebSocket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'message') {
            // Display incoming messages from task execution
            addMessage(data.content, data.message_type || 'system', new Date(data.timestamp));
        }
        else if (data.type === 'task_update') {
            const task = data.task;
            
            // Update task status in history
            const taskItem = document.getElementById(`task-${taskId}`);
            if (taskItem) {
                taskItem.querySelector('.task-status').textContent = task.status;
            }
            
            // Update status indicator
            if (task.status === 'running') {
                document.getElementById('taskStatusIndicator').innerHTML = '<span class="loading"></span>';
            } else {
                document.getElementById('taskStatusIndicator').textContent = '';
            }
        } 
        else if (data.type === 'task_complete') {
            addMessage(`Task completed with status: ${data.status}`, 'system');
            taskWebSocket.close();
            
            addMessage(`Please send a new task or command when ready.`, 'system');
        }
        else if (data.type === 'error') {
            addMessage(`Task error: ${data.message}`, 'system');
            taskWebSocket.close();
        }

    };
    
    taskWebSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket readyState:', taskWebSocket.readyState);
        addMessage('WebSocket connection error - check console', 'system');
    };
    
    taskWebSocket.onclose = () => {
        console.log('WebSocket disconnected');
    };
}

// ====================================================================
// VNC Operations
// ====================================================================

function toggleViewOnly() {
    const btn = document.getElementById('viewOnlyBtn');
    const iframe = document.getElementById('vncFrame');
    
    const isViewOnly = iframe.src.includes('view_only=1');
    
    if (isViewOnly) {
        // Enable interaction
        iframe.src = iframe.src.replace('view_only=1', 'view_only=0');
        btn.textContent = 'View Only: Off';
        btn.classList.add('active');
        addMessage('VNC interaction enabled - you can now control the desktop', 'system');
    } else {
        // Disable interaction
        iframe.src = iframe.src.replace('view_only=0', 'view_only=1');
        btn.textContent = 'View Only: On';
        btn.classList.remove('active');
        addMessage('VNC switched to view-only mode', 'system');
    }
}

// ====================================================================
// File Management
// ====================================================================

function updateFileList(files) {
    const fileListDiv = document.getElementById('fileList');
    
    if (!files || files.length === 0) {
        fileListDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #999; font-size: 11px;">No files tracked yet</div>';
        return;
    }
    
    fileListDiv.innerHTML = files.map(file => `
        <div class="file-item">
            <span><span class="file-icon">📄</span>${file.name}</span>
            <span style="color:#999;font-size:10px;">${file.size || ''}</span>
        </div>
    `).join('');
}

// ====================================================================
// Chat Input Handler
// ====================================================================

function setupChatInputHandler() {
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) return;
    
    chatInput.addEventListener('keydown', (e) => {
        // Enter sends message, Shift+Enter creates newline
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Display user message
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Reset textarea height
    chatInput.style.height = '60px';
    
    // TODO: Send message to backend if needed
    addMessage('Chat message feature - backend integration ready', 'system');
}

function captureScreenshot() {
    // Placeholder for screenshot capture functionality
    // This would fetch the latest screenshot from the VNC display
    console.log('Screenshot capture initialized');
}

// ====================================================================
// Initialization
// ===================================================================="

document.addEventListener('DOMContentLoaded', () => {
    // Initialize VNC display assignment FIRST - before any other initialization
    initializeVNCDisplay();
    
    // Setup chat input handler
    setupChatInputHandler();
    
    // Try to reconnect to existing session
    listSessions();
    
    // Initial screenshot
    captureScreenshot();
    
    // Log tab session ID for debugging
    console.log('Tab Session ID:', tabSessionId);
});

// Cleanup intervals on page unload (now handled in beforeunload above)
