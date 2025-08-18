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
                port: '11434', // Changed default port to 11434 (Ollama default)
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
        this.goToStep = this.goToStep.bind(this);
        this.disconnectButtplug = this.disconnectButtplug.bind(this);
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
        
        // Set up step navigation listeners
        document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                const stepNum = index + 1;
                // Allow navigation to any step for better UX
                this.goToStep(stepNum);
            });
        });
        
        // Set up disconnect buttons if they exist
        const disconnectButtplugBtn = document.getElementById('disconnect-buttplug-btn');
        if (disconnectButtplugBtn) {
            disconnectButtplugBtn.addEventListener('click', this.disconnectButtplug);
        }
        
        // Check the initial connection status with the server
        await this.#checkInitialStatus();

        // Initialize the UI
        this.renderCurrentStep();
    }

    /**
     * Navigate to a specific step
     */
    goToStep(stepNumber) {
        this.state.currentStep = stepNumber;
        this.renderCurrentStep();
        this.saveSettings();
    }

    /**
     * Check the initial connection status from the server
     * and update the state accordingly.
     */
    async #checkInitialStatus() {
        try {
            const response = await fetch('/setup/status');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const status = await response.json();

            this.state.buttplug.connected = !!status.buttplug_connected;
            this.state.llama.connected = !!status.llama_connected;

            // Update currentStep based on actual connection status
            // Only go to step 3 if both are connected
            if (this.state.buttplug.connected && this.state.llama.connected) {
                this.state.currentStep = 3;
            } 
            // Go to step 2 if buttplug is connected
            else if (this.state.buttplug.connected) {
                this.state.currentStep = 2;
            } 
            // Otherwise start at step 1
            else {
                this.state.currentStep = 1;
            }

            this.saveSettings();
        } catch (error) {
            console.error('Error checking initial status:', error);
            // On error, start at step 1
            this.state.currentStep = 1;
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
        
        // Update form fields with current settings
        if (this.state.currentStep === 1) {
            document.getElementById('buttplug-host').value = this.state.buttplug.host;
            document.getElementById('buttplug-port').value = this.state.buttplug.port;
            
            // Update connection status display
            const statusElement = document.getElementById('buttplug-status');
            if (statusElement) {
                if (this.state.buttplug.connected) {
                    statusElement.innerHTML = '✅ <strong>Connected!</strong>';
                    statusElement.className = 'connection-status text-success';
                } else {
                    statusElement.textContent = 'Not Connected';
                    statusElement.className = 'connection-status disconnected';
                }
            }
        } else if (this.state.currentStep === 2) {
            document.getElementById('llama-host').value = this.state.llama.host;
            document.getElementById('llama-port').value = this.state.llama.port;
            document.getElementById('llama-api-key').value = this.state.llama.apiKey;
            
            // Update connection status display
            const statusElement = document.getElementById('llama-status');
            if (statusElement) {
                if (this.state.llama.connected) {
                    statusElement.innerHTML = '✅ <strong>Connected!</strong>';
                    statusElement.className = 'connection-status text-success';
                } else {
                    statusElement.textContent = 'Not Connected';
                    statusElement.className = 'connection-status disconnected';
                }
            }
        }
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
        const buttplugBtn = document.getElementById('connect-buttplug-btn');
        if (buttplugBtn) {
            buttplugBtn.disabled = false; // Always enable for reconnection
            buttplugBtn.innerHTML = this.state.buttplug.connected ? 
                '<i class="bi bi-arrow-repeat me-2"></i>Reconnect' : 
                '<i class="bi bi-plug me-2"></i>Connect to Intiface Central';
        }
        
        const disconnectButtplugBtn = document.getElementById('disconnect-buttplug-btn');
        if (disconnectButtplugBtn) {
            disconnectButtplugBtn.style.display = this.state.buttplug.connected ? 'block' : 'none';
        }

        const llamaBtn = document.getElementById('connect-llama-btn');
        if (llamaBtn) {
            llamaBtn.disabled = !this.state.buttplug.connected; // Only enable if buttplug is connected
            llamaBtn.innerHTML = this.state.llama.connected ? 
                '<i class="bi bi-arrow-repeat me-2"></i>Reconnect' : 
                '<i class="bi bi-cpu me-2"></i>Connect to Llama Server';
        }

        document.getElementById('start-ai-btn').disabled = !(this.state.buttplug.connected && this.state.llama.connected);
        
        // Update progress bar
        const progressBar = document.querySelector('.progress-bar');
        const progressPercentage = ((this.state.currentStep - 1) / 2) * 100;
        progressBar.style.width = `${progressPercentage}%`;
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
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Connecting...';

            // Show connecting status
            if (statusElement) {
                statusElement.textContent = 'Connecting to server...';
                statusElement.className = 'connection-status text-info';
            }
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
                this.state.buttplug.host = host;
                this.state.buttplug.port = port;
                this.state.buttplug.device = data.device || null;
                this.saveSettings();
                
                // Update status UI
                if (statusElement) {
                    statusElement.innerHTML = '✅ <strong>Connected!</strong>';
                    statusElement.className = 'connection-status text-success';
                }
                
                // Show success message
                const deviceInfo = data.device ? ` (${data.device.name})` : '';
                this.showNotification(`✅ Successfully connected to Buttplug server${deviceInfo}`, 'success');
                
                // Update button state
                this.updateNavigation();
                
            } else {
                throw new Error(data.error || 'Failed to connect to Buttplug server');
            }
        } catch (error) {
            console.error('Buttplug connection error:', error);
            if (statusElement) {
                statusElement.textContent = `Error: ${error.message}`;
                statusElement.className = 'connection-status text-danger';
            }
            this.showNotification(`❌ ${error.message}`, 'error');
        } finally {
            // Reset button state
            const btn = document.getElementById('connect-buttplug-btn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = this.state.buttplug.connected ? 
                    '<i class="bi bi-arrow-repeat me-2"></i>Reconnect' : 
                    '<i class="bi bi-plug me-2"></i>Connect to Intiface Central';
            }
        }
    }

    /**
     * Disconnect from Buttplug server
     */
    async disconnectButtplug() {
        try {
            // For now, just update the local state
            // In a real implementation, you might want to call a disconnect endpoint
            this.state.buttplug.connected = false;
            this.state.buttplug.device = null;
            this.saveSettings();
            
            // Update UI
            const statusElement = document.getElementById('buttplug-status');
            if (statusElement) {
                statusElement.textContent = 'Not Connected';
                statusElement.className = 'connection-status disconnected';
            }
            
            this.updateNavigation();
            this.showNotification('🔌 Disconnected from Buttplug server', 'info');
        } catch (error) {
            console.error('Buttplug disconnection error:', error);
            this.showNotification(`❌ Error disconnecting: ${error.message}`, 'error');
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
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Connecting...';

            // Call backend to connect to Llama
            const response = await fetch('/connect_llama', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port, apiKey })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.state.llama.connected = true;
                this.saveSettings();
                
                // Update UI
                const statusElement = document.getElementById('llama-status');
                if (statusElement) {
                    statusElement.innerHTML = '✅ <strong>Connected!</strong>';
                    statusElement.className = 'connection-status text-success';
                }
                
                this.updateNavigation();
                
                // Show success message
                this.showNotification('✅ Successfully connected to Llama server', 'success');
            } else {
                throw new Error(data.error || 'Failed to connect to Llama server');
            }
        } catch (error) {
            console.error('Llama connection error:', error);
            
            // Update UI with error
            const statusElement = document.getElementById('llama-status');
            if (statusElement) {
                statusElement.textContent = `Error: ${error.message}`;
                statusElement.className = 'connection-status text-danger';
            }
            
            this.showNotification(`❌ ${error.message}`, 'error');
        } finally {
            // Reset button state
            const btn = document.getElementById('connect-llama-btn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = this.state.llama.connected ? 
                    '<i class="bi bi-arrow-repeat me-2"></i>Reconnect' : 
                    '<i class="bi bi-cpu me-2"></i>Connect to Llama Server';
            }
        }
    }

    /**
     * Start AI operations
     */
    startAIOperations() {
        if (this.state.buttplug.connected && this.state.llama.connected) {
            // Hide setup UI and show main application
            document.getElementById('setup-container').style.display = 'none';
            // In a real implementation, we would redirect to the main app
            // For now, we'll just show a success message
            this.showNotification('✅ Setup complete! You can now use StrokeGPT.', 'success');
        }
    }

    /**
     * Show a notification message
     */
    showNotification(message, type = 'info') {
        // Check if we're in the setup page or main app
        const notificationsContainer = document.getElementById('notifications-container') || document.body;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notificationsContainer.appendChild(notification);
        
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