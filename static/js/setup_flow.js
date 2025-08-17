/**
 * Setup Flow Manager for StrokeGPT
 * Handles the staged setup process for Buttplug and Llama connections
 */

class SetupFlow {
    constructor() {
        // Setup state
        this.state = {
            buttplug: {
                connected: false,
                host: 'ws://127.0.0.1',
                port: '12345',
                device: null
            },
            llama: {
                connected: false,
                host: 'http://localhost',
                port: '8000',
                apiKey: ''
            },
            currentStep: 1 // 1 = Buttplug setup, 2 = Llama setup, 3 = Ready
        };

        // Bind methods
        this.init = this.init.bind(this);
        this.renderCurrentStep = this.renderCurrentStep.bind(this);
        this.connectButtplug = this.connectButtplug.bind(this);
        this.connectLlama = this.connectLlama.bind(this);
        this.startAIOperations = this.startAIOperations.bind(this);
    }

    /**
     * Initialize the setup flow
     */
    async init() {
        // Load saved settings if any
        this.loadSettings();
        
        // Set up event listeners
        document.getElementById('connect-buttplug-btn').addEventListener('click', this.connectButtplug);
        document.getElementById('connect-llama-btn').addEventListener('click', this.connectLlama);
        document.getElementById('start-ai-btn').addEventListener('click', this.startAIOperations);
        
        // Check the initial connection status with the server
        await this.#checkInitialStatus();

        // Initialize the UI
        this.renderCurrentStep();
    }

    /**
     * Check the initial connection status from the server
     * and update the state accordingly.
     */
    async #checkInitialStatus() {
        try {
            const response = await fetch('/status');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const status = await response.json();

            this.state.buttplug.connected = !!status.buttplug_connected;
            this.state.llama.connected = !!status.llama_connected;

            // Optionally, update currentStep if both are connected
            if (this.state.buttplug.connected && this.state.llama.connected) {
                this.state.currentStep = 3;
            } else if (this.state.buttplug.connected) {
                this.state.currentStep = 2;
            } else {
                this.state.currentStep = 1;
            }

            this.saveSettings();
        } catch (error) {
            console.error('Error checking initial status:', error);
        }
    }

    /**
     * Load saved settings from localStorage
     */
    loadSettings() {
        const savedSettings = localStorage.getItem('strokeGPT_settings');
        if (savedSettings) {
            try {
                const settings = JSON.parse(savedSettings);
                if (settings.buttplug) this.state.buttplug = { ...this.state.buttplug, ...settings.buttplug };
                if (settings.llama) this.state.llama = { ...this.state.llama, ...settings.llama };
            } catch (e) {
                console.error('Error loading settings:', e);
            }
        }
    }

    /**
     * Save current settings to localStorage
     */
    saveSettings() {
        const settings = {
            buttplug: this.state.buttplug,
            llama: this.state.llama
        };
        localStorage.setItem('strokeGPT_settings', JSON.stringify(settings));
    }

    /**
     * Render the current setup step
     */
    renderCurrentStep() {
        // Hide all steps first
        document.querySelectorAll('.setup-step').forEach(step => {
            step.style.display = 'none';
        });

        // Show current step
        const currentStepEl = document.getElementById(`setup-step-${this.state.currentStep}`);
        if (currentStepEl) {
            currentStepEl.style.display = 'block';
        }

        // Update navigation/status
        this.updateNavigation();
    }

    /**
     * Update navigation buttons and status indicators
     */
    updateNavigation() {
        // Update step indicators
        document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.toggle('active', stepNum === this.state.currentStep);
            indicator.classList.toggle('completed', 
                (stepNum === 1 && this.state.buttplug.connected) ||
                (stepNum === 2 && this.state.llama.connected)
            );
        });

        // Update button states
        document.getElementById('connect-buttplug-btn').disabled = this.state.buttplug.connected;
        document.getElementById('connect-llama-btn').disabled = this.state.llama.connected || !this.state.buttplug.connected;
        document.getElementById('start-ai-btn').disabled = !(this.state.buttplug.connected && this.state.llama.connected);
    }

    /**
     * Connect to Buttplug server
     */
    async connectButtplug() {
        const host = document.getElementById('buttplug-host').value;
        const port = document.getElementById('buttplug-port').value;
        const btn = document.getElementById('connect-buttplug-btn');
        const statusElement = document.getElementById('buttplug-status');
        
        try {
            // Update button and UI state
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Connecting...';
            statusElement.textContent = 'Connecting to server...';
            statusElement.className = 'text-info';

            // Show connecting status
            this.showNotification('🔌 Connecting to Buttplug server...', 'info');

            // Call backend to connect to Buttplug
            const response = await fetch('/connect_buttplug', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.state.buttplug.connected = true;
                this.state.buttplug.device = data.device || null;
                this.saveSettings();
                
                // Update status UI
                statusElement.innerHTML = '✅ <strong>Connected!</strong>';
                statusElement.className = 'text-success';
                
                // Show success message
                const deviceInfo = data.device ? ` (${data.device.name})` : '';
                this.showNotification(`✅ Successfully connected to Buttplug server${deviceInfo}`, 'success');
                
                // Move to next step after a short delay
                setTimeout(() => {
                    this.state.currentStep = 2;
                    this.renderCurrentStep();
                }, 1000);
                
            } else {
                throw new Error(data.error || 'Failed to connect to Buttplug server');
            }
        } catch (error) {
            console.error('Buttplug connection error:', error);
            statusElement.textContent = `Error: ${error.message}`;
            statusElement.className = 'text-danger';
            this.showNotification(`❌ ${error.message}`, 'error');
        } finally {
            // Reset button state
            const btn = document.getElementById('connect-buttplug-btn');
            if (btn) {
                btn.disabled = this.state.buttplug.connected;
                btn.innerHTML = this.state.buttplug.connected ? 
                    '<i class="bi bi-check-circle me-2"></i>Connected' : 
                    '<i class="bi bi-plug me-2"></i>Connect';
            }
        }
    }

    /**
     * Connect to Llama server
     */
    async connectLlama() {
        const host = document.getElementById('llama-host').value;
        const port = document.getElementById('llama-port').value;
        const apiKey = document.getElementById('llama-api-key').value;
        
        // Update state
        this.state.llama.host = host;
        this.state.llama.port = port;
        this.state.llama.apiKey = apiKey;
        this.saveSettings();

        try {
            // Show loading state
            const btn = document.getElementById('connect-llama-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Connecting...';

            // Call backend to connect to Llama
            const response = await fetch('/connect_llama', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port, apiKey })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.state.llama.connected = true;
                this.saveSettings();
                
                // Move to next step
                this.state.currentStep = 3;
                this.renderCurrentStep();
                
                // Show success message
                this.showNotification('✅ Successfully connected to Llama server', 'success');
            } else {
                throw new Error(data.error || 'Failed to connect to Llama server');
            }
        } catch (error) {
            console.error('Llama connection error:', error);
            this.showNotification(`❌ ${error.message}`, 'error');
        } finally {
            // Reset button state
            const btn = document.getElementById('connect-llama-btn');
            btn.disabled = this.state.llama.connected;
            btn.textContent = this.state.llama.connected ? 'Connected' : originalText;
        }
    }

    /**
     * Start AI operations
     */
    startAIOperations() {
        if (this.state.buttplug.connected && this.state.llama.connected) {
            // Hide setup UI and show main application
            document.getElementById('setup-container').style.display = 'none';
            document.getElementById('main-application').style.display = 'block';
            
            // Emit event that setup is complete
            const event = new CustomEvent('setupComplete', { 
                detail: { 
                    buttplug: this.state.buttplug,
                    llama: this.state.llama
                } 
            });
            document.dispatchEvent(event);
        }
    }

    /**
     * Show a notification message
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        const container = document.getElementById('notifications-container');
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}

// Initialize the setup flow when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const setupFlow = new SetupFlow();
    window.setupFlow = setupFlow; // Make it accessible globally for debugging
    setupFlow.init();
});

// DOM Elements
const setupContainer = document.getElementById('setup-container');
const progressSteps = document.querySelectorAll('.step-indicator');
const setupSteps = document.querySelectorAll('.setup-step');
const nextButtons = document.querySelectorAll('[data-next]');
const prevButtons = document.querySelectorAll('[data-prev]');

// Form elements
const buttplugConnectBtn = document.getElementById('connect-buttplug-btn');
const buttplugHostInput = document.getElementById('buttplug-host');
const buttplugPortInput = document.getElementById('buttplug-port');
const buttplugStatus = document.getElementById('buttplug-status');

const llamaConnectBtn = document.getElementById('connect-llama-btn');
const llamaHostInput = document.getElementById('llama-host');
const llamaPortInput = document.getElementById('llama-port');
const llamaApiKeyInput = document.getElementById('llama-api-key');
const llamaStatus = document.getElementById('llama-status');

const startAiBtn = document.getElementById('start-ai-btn');

// Current step tracking
let currentStep = 1;
const totalSteps = 3;

// Connection states
let isButtplugConnected = false;
let isLlamaConnected = false;

// Initialize the setup process
function initSetup() {
    // Load saved settings if they exist
    loadSettings();
    
    // Set up event listeners
    setupEventListeners();
    
    // Show the first step
    updateProgress();
    showStep(currentStep);
    
    // Check initial connection status
    // checkConnectionStatus(); // Removed: now handled by SetupFlow class
}

// Set up event listeners
function setupEventListeners() {
    // Connect to Buttplug button
    if (buttplugConnectBtn) {
        buttplugConnectBtn.addEventListener('click', handleButtplugConnect);
    }
    
    // Connect to Llama button
    if (llamaConnectBtn) {
        llamaConnectBtn.addEventListener('click', handleLlamaConnect);
    }
    
    // Start AI button
    if (startAiBtn) {
        startAiBtn.addEventListener('click', handleStartAi);
    }
    
    // Next/Previous buttons
    nextButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (validateStep(currentStep)) {
                currentStep++;
                updateProgress();
                showStep(currentStep);
            }
        });
    });
    
    prevButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentStep--;
            updateProgress();
            showStep(currentStep);
        });
    });
    
    // Input field changes
    [buttplugHostInput, buttplugPortInput, llamaHostInput, llamaPortInput, llamaApiKeyInput].forEach(input => {
        if (input) {
            input.addEventListener('change', saveSettings);
            input.addEventListener('blur', saveSettings);
        }
    });
}

// Handle Buttplug connection
async function handleButtplugConnect() {
    if (isButtplugConnected) {
        // Already connected, disconnect
        try {
            const response = await fetch('/disconnect_buttplug', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                updateButtplugStatus(false);
                showNotification('Disconnected from Buttplug server', 'info');
            } else {
                throw new Error(result.error || 'Failed to disconnect from Buttplug server');
            }
        } catch (error) {
            console.error('Error disconnecting from Buttplug:', error);
            showNotification(`Error: ${error.message}`, 'error');
        }
    } else {
        // Connect to Buttplug
        const host = buttplugHostInput.value.trim();
        const port = buttplugPortInput.value.trim();
        
        if (!host || !port) {
            showNotification('Please enter both host and port', 'warning');
            return;
        }
        
        setButtonLoading(buttplugConnectBtn, true);
        
        try {
            const response = await fetch('/connect_buttplug', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    host: host,
                    port: port
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                updateButtplugStatus(true);
                showNotification('Successfully connected to Buttplug server', 'success');
                saveSettings();
                
                // Auto-advance to next step if not on last step
                if (currentStep === 1) {
                    setTimeout(() => {
                        currentStep++;
                        updateProgress();
                        showStep(currentStep);
                    }, 1000);
                }
            } else {
                throw new Error(result.error || 'Failed to connect to Buttplug server');
            }
        } catch (error) {
            console.error('Error connecting to Buttplug:', error);
            showNotification(`Error: ${error.message}`, 'error');
        } finally {
            setButtonLoading(buttplugConnectBtn, false);
        }
    }
}

// Handle Llama connection
async function handleLlamaConnect() {
    if (isLlamaConnected) {
        // Already connected, disconnect
        try {
            const response = await fetch('/disconnect_llama', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                updateLlamaStatus(false);
                showNotification('Disconnected from Llama server', 'info');
            } else {
                throw new Error(result.error || 'Failed to disconnect from Llama server');
            }
        } catch (error) {
            console.error('Error disconnecting from Llama:', error);
            showNotification(`Error: ${error.message}`, 'error');
        }
    } else {
        // Connect to Llama
        const host = llamaHostInput.value.trim();
        const port = llamaPortInput.value.trim();
        const apiKey = llamaApiKeyInput.value.trim();
        
        if (!host || !port) {
            showNotification('Please enter both host and port', 'warning');
            return;
        }
        
        setButtonLoading(llamaConnectBtn, true);
        
        try {
            const response = await fetch('/connect_llama', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    host: host,
                    port: port,
                    api_key: apiKey
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                updateLlamaStatus(true);
                showNotification('Successfully connected to Llama server', 'success');
                saveSettings();
                
                // Auto-advance to next step if not on last step
                if (currentStep === 2) {
                    setTimeout(() => {
                        currentStep++;
                        updateProgress();
                        showStep(currentStep);
                    }, 1000);
                }
            } else {
                throw new Error(result.error || 'Failed to connect to Llama server');
            }
        } catch (error) {
            console.error('Error connecting to Llama:', error);
            showNotification(`Error: ${error.message}`, 'error');
        } finally {
            setButtonLoading(llamaConnectBtn, false);
        }
    }
}

// Handle Start AI button click
function handleStartAi() {
    // Redirect to the main app
    window.location.href = '/';
}

// Update the progress indicators
function updateProgress() {
    // Update progress bar
    const progressBar = document.querySelector('.progress-bar');
    const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100;
    progressBar.style.width = `${progressPercentage}%`;
    
    // Update step indicators
    progressSteps.forEach((step, index) => {
        if (index + 1 < currentStep) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else if (index + 1 === currentStep) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });
    
    // Update progress steps container class for line animation
    const stepsContainer = document.querySelector('.progress-steps');
    stepsContainer.className = `progress-steps active-${currentStep}`;
}

// Show the specified step
function showStep(stepNumber) {
    // Hide all steps
    setupSteps.forEach(step => {
        step.classList.remove('active');
    });
    
    // Show the current step
    const currentStepElement = document.getElementById(`step-${stepNumber}`);
    if (currentStepElement) {
        currentStepElement.classList.add('active');
    }
    
    // Scroll to top of the step
    setupContainer.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Validate the current step before proceeding
function validateStep(stepNumber) {
    switch (stepNumber) {
        case 1:
            return isButtplugConnected;
        case 2:
            return isLlamaConnected;
        default:
            return true;
    }
}

// Update Buttplug connection status in UI
function updateButtplugStatus(connected) {
    isButtplugConnected = connected;
    
    if (buttplugConnectBtn) {
        buttplugConnectBtn.textContent = connected ? 'Disconnect' : 'Connect';
        buttplugConnectBtn.classList.toggle('connected', connected);
    }
    
    if (buttplugStatus) {
        buttplugStatus.textContent = connected ? 'Connected' : 'Not Connected';
        buttplugStatus.className = 'connection-status ' + (connected ? 'connected' : 'disconnected');
    }
    
    // Enable/disable next button based on connection status
    const nextButton = document.querySelector(`[data-next="${currentStep}"]`);
    if (nextButton) {
        nextButton.disabled = !connected;
    }
}

// Update Llama connection status in UI
function updateLlamaStatus(connected) {
    isLlamaConnected = connected;
    
    if (llamaConnectBtn) {
        llamaConnectBtn.textContent = connected ? 'Disconnect' : 'Connect';
        llamaConnectBtn.classList.toggle('connected', connected);
    }
    
    if (llamaStatus) {
        llamaStatus.textContent = connected ? 'Connected' : 'Not Connected';
        llamaStatus.className = 'connection-status ' + (connected ? 'connected' : 'disconnected');
    }
    
    // Enable/disable next button based on connection status
    const nextButton = document.querySelector(`[data-next="${currentStep}"]`);
    if (nextButton) {
        nextButton.disabled = !connected;
    }
}


// Load saved settings from localStorage
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('strokegpt_settings') || '{}');
    
    // Load Buttplug settings
    if (settings.buttplug) {
        if (buttplugHostInput) buttplugHostInput.value = settings.buttplug.host || 'ws://127.0.0.1';
        if (buttplugPortInput) buttplugPortInput.value = settings.buttplug.port || '12345';
    }
    
    // Load Llama settings
    if (settings.llama) {
        if (llamaHostInput) llamaHostInput.value = settings.llama.host || 'http://localhost';
        if (llamaPortInput) llamaPortInput.value = settings.llama.port || '11434';
        if (llamaApiKeyInput) llamaApiKeyInput.value = settings.llama.apiKey || '';
    }
}

// Save settings to localStorage
function saveSettings() {
    const settings = {
        buttplug: {
            host: buttplugHostInput ? buttplugHostInput.value.trim() : 'ws://127.0.0.1',
            port: buttplugPortInput ? buttplugPortInput.value.trim() : '12345'
        },
        llama: {
            host: llamaHostInput ? llamaHostInput.value.trim() : 'http://localhost',
            port: llamaPortInput ? llamaPortInput.value.trim() : '11434',
            apiKey: llamaApiKeyInput ? llamaApiKeyInput.value.trim() : ''
        }
    };
    
    localStorage.setItem('strokegpt_settings', JSON.stringify(settings));
}

// Show notification to user
function showNotification(message, type = 'info') {
    // Simple notification implementation - can be enhanced with a proper notification system
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Set button loading state
function setButtonLoading(button, isLoading) {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span> Connecting...';
    } else {
        button.disabled = false;
        // Restore original text based on connection state
        if (button === buttplugConnectBtn) {
            button.textContent = isButtplugConnected ? 'Disconnect' : 'Connect';
        } else if (button === llamaConnectBtn) {
            button.textContent = isLlamaConnected ? 'Disconnect' : 'Connect';
        }
    }
}

// Add notification styles
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    .notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        transform: translateY(100px);
        opacity: 0;
        transition: transform 0.3s ease, opacity 0.3s ease;
    }
    
    .notification.show {
        transform: translateY(0);
        opacity: 1;
    }
    
    .notification.fade-out {
        transform: translateY(-20px);
        opacity: 0;
    }
    
    .notification.success {
        background-color: #10b981;
    }
    
    .notification.error {
        background-color: #ef4444;
    }
    
    .notification.warning {
        background-color: #f59e0b;
    }
    
    .notification.info {
        background-color: #3b82f6;
    }
    
    .spinner {
        display: inline-block;
        width: 12px;
        height: 12px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
        margin-right: 8px;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .connection-status {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 8px;
    }
    
    .connection-status.connected {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    
    .connection-status.disconnected {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    .btn.connected {
        background-color: #10b981;
    }
    
    .btn.connected:hover:not(:disabled) {
        background-color: #0d9f6e;
    }
`;

document.head.appendChild(notificationStyles);

// Initialize the setup when the DOM is loaded
document.addEventListener('DOMContentLoaded', initSetup);
