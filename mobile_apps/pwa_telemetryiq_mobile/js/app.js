// TelemetryIQ Mobile PWA Main Application
// Matches desktop UI theme and functionality

const API_BASE_URL = 'http://192.168.1.100:8000';
const WS_URL = 'ws://192.168.1.100:8000/ws/telemetry';

// Initialize services
const api = new TelemetryIQAPI(API_BASE_URL);
const ws = new TelemetryIQWebSocket(WS_URL);

// Application state
let currentTelemetry = {};
let currentTab = 'dashboard';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    setupNavigation();
    setupWebSocket();
    setupConfigForm();
    setupAIChat();
    loadConfigHistory();
    
    // Initial telemetry fetch
    refreshTelemetry();
    setInterval(refreshTelemetry, 5000); // Fallback polling every 5 seconds
}

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.dataset.tab;
            switchTab(tab);
            
            // Update nav active state
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    // Show selected tab
    const tab = document.getElementById(`${tabName}Tab`);
    if (tab) {
        tab.classList.add('active');
        currentTab = tabName;
        
        // Refresh tab-specific data
        if (tabName === 'config') {
            loadConfigHistory();
        }
    }
}

// WebSocket connection
function setupWebSocket() {
    ws.on('connected', () => {
        updateConnectionStatus(true);
    });
    
    ws.on('disconnected', () => {
        updateConnectionStatus(false);
    });
    
    ws.on('telemetry', (data) => {
        currentTelemetry = data;
        updateTelemetryDisplay(data);
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    });
    
    ws.connect();
}

function updateConnectionStatus(connected) {
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    if (connected) {
        indicator.classList.add('connected');
        statusText.textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        statusText.textContent = 'Disconnected';
    }
}

// Telemetry display
async function refreshTelemetry() {
    try {
        const response = await api.getCurrentTelemetry();
        if (response.data) {
            currentTelemetry = response.data;
            updateTelemetryDisplay(response.data);
        }
    } catch (error) {
        console.error('Error refreshing telemetry:', error);
    }
}

function updateTelemetryDisplay(data) {
    // Update telemetry grid
    const grid = document.getElementById('telemetryGrid');
    grid.innerHTML = '';
    
    Object.entries(data).forEach(([key, value]) => {
        const card = document.createElement('div');
        card.className = 'telemetry-card';
        card.innerHTML = `
            <div class="telemetry-card-label">${key}</div>
            <div class="telemetry-card-value">${value.toFixed(1)}</div>
        `;
        grid.appendChild(card);
    });
    
    // Update key metrics
    updateGauge('rpm', data.RPM || 0, 0, 8000);
    updateGauge('boost', data.Boost_Pressure || 0, -5, 30);
    updateGauge('afr', data.AFR || 0, 10, 20);
    updateGauge('coolant', data.Coolant_Temp || 0, 70, 120);
}

function updateGauge(name, value, min, max) {
    const valueEl = document.getElementById(`${name}Value`);
    const progressEl = document.getElementById(`${name}Progress`);
    
    if (valueEl) {
        valueEl.textContent = value.toFixed(1);
    }
    
    if (progressEl) {
        const percentage = ((value - min) / (max - min)) * 100;
        progressEl.style.width = `${Math.max(0, Math.min(100, percentage))}%`;
        
        // Update color based on status
        progressEl.className = 'gauge-fill';
        if (percentage < 30) {
            progressEl.classList.add('optimal');
        } else if (percentage < 70) {
            progressEl.classList.add('adjustable');
        } else {
            progressEl.classList.add('critical');
        }
    }
}

// Configuration management
function setupConfigForm() {
    const form = document.getElementById('configForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const changeType = document.getElementById('changeType').value;
        const category = document.getElementById('category').value;
        const parameter = document.getElementById('parameter').value;
        const newValue = parseFloat(document.getElementById('newValue').value);
        const oldValue = document.getElementById('oldValue').value 
            ? parseFloat(document.getElementById('oldValue').value) 
            : null;
        
        try {
            const result = await api.applyConfigChange(
                changeType,
                category,
                parameter,
                newValue,
                oldValue
            );
            
            if (result.warnings && result.warnings.length > 0) {
                displayWarnings(result.warnings);
            } else {
                alert('Configuration change applied successfully');
                form.reset();
                loadConfigHistory();
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
}

function displayWarnings(warnings) {
    const container = document.getElementById('configWarnings');
    container.innerHTML = '';
    
    warnings.forEach(warning => {
        const div = document.createElement('div');
        div.className = `warning-item ${warning.severity}`;
        div.innerHTML = `
            <div class="warning-message">${warning.message}</div>
            ${warning.suggestion ? `<div class="warning-suggestion">💡 ${warning.suggestion}</div>` : ''}
        `;
        container.appendChild(div);
    });
}

async function loadConfigHistory() {
    try {
        const history = await api.getConfigHistory();
        const container = document.getElementById('configHistory');
        container.innerHTML = '';
        
        if (history.length === 0) {
            container.innerHTML = '<div class="loading">No configuration history</div>';
            return;
        }
        
        history.forEach(change => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="history-header">
                    <div class="history-parameter">${change.parameter}</div>
                    <div class="history-category">${change.category}</div>
                </div>
                <div class="history-change">${change.old_value} → ${change.new_value}</div>
            `;
            container.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading config history:', error);
    }
}

// AI Advisor chat
function setupAIChat() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendButton');
    const messagesContainer = document.getElementById('chatMessages');
    
    function addMessage(content, isUser) {
        const message = document.createElement('div');
        message.className = `chat-message ${isUser ? 'user' : 'assistant'}`;
        message.textContent = content;
        messagesContainer.appendChild(message);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async function sendMessage() {
        const question = input.value.trim();
        if (!question) return;
        
        addMessage(question, true);
        input.value = '';
        
        try {
            const response = await api.askAIAdvisor(question);
            addMessage(response.response || 'No response', false);
        } catch (error) {
            addMessage(`Error: ${error.message}`, false);
        }
    }
    
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// Service Worker registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('Service Worker registered:', registration);
            })
            .catch(error => {
                console.error('Service Worker registration failed:', error);
            });
    });
}
















