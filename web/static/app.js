/**
 * Medical Research AI - Frontend JavaScript
 * Handles voice recording, WebSocket connections, and UI interactions
 */

class MedicalResearchApp {
    constructor() {
        this.healthWs = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;

        // WebSocket reconnection properties
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.connectionStatus = 'disconnected';

        // Progress tracking
        this.currentConsultationId = null;
        this.progressSteps = [
            'initializing',
            'analyzing_symptoms',
            'generating_questions',
            'processing_responses',
            'generating_diagnosis',
            'recommending_treatments',
            'finalizing_results'
        ];
        this.currentStep = 0;

        this.init();
    }
    
    init() {
        this.initHealthWebSocket();
        this.setupEventListeners();
        this.setupAudioVisualization();
    }
    
    // WebSocket Health Monitoring
    initHealthWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.healthWs = new WebSocket(`${protocol}//${window.location.host}/ws/health`);

        this.healthWs.onopen = () => {
            console.log('Health WebSocket connected');
            this.updateConnectionStatus('connected');
            this.reconnectAttempts = 0;
        };

        this.healthWs.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.healthWs.onclose = (event) => {
            console.log('Health WebSocket closed, code:', event.code);
            this.updateConnectionStatus('disconnected');
            this.scheduleReconnect();
        };

        this.healthWs.onerror = (error) => {
            console.error('Health WebSocket error:', error);
            this.updateConnectionStatus('error');
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'health_update':
                this.updateHealthPanel(data.data);
                break;
            case 'consultation_progress':
                this.updateConsultationProgress(data.data);
                break;
            case 'diagnosis_complete':
                this.handleDiagnosisComplete(data.data);
                break;
            case 'emergency_alert':
                this.showEmergencyAlert(data.data);
                break;
            case 'system_notification':
                this.showSystemNotification(data.data);
                break;
            case 'error':
                console.error('WebSocket error:', data.message);
                this.showErrorNotification(data.message);
                break;
            default:
                console.warn('Unknown WebSocket message type:', data.type);
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            this.reconnectAttempts++;

            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.initHealthWebSocket(), delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
        }
    }
    
    updateHealthPanel(healthData) {
        const panel = document.getElementById('health-panel');
        const statusHeader = document.getElementById('health-status');
        
        if (!panel || !statusHeader) return;
        
        let html = '';
        let overallStatus = healthData.health_status || 'unknown';
        
        // Voice interface status
        const voiceAvailable = healthData.voice_interface_available;
        const statusColor = voiceAvailable ? 'green' : 'yellow';
        const statusText = voiceAvailable ? 'Available' : 'Degraded';
        
        html += `
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Voice Interface</span>
                <div class="flex items-center space-x-2">
                    <span class="text-xs text-gray-500">${statusText}</span>
                    <div class="w-2 h-2 bg-${statusColor}-500 rounded-full"></div>
                </div>
            </div>
        `;
        
        // Supported languages
        if (healthData.supported_languages && healthData.supported_languages.length > 0) {
            html += `
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-600">Languages</span>
                    <span class="text-xs text-gray-500">${healthData.supported_languages.join(', ')}</span>
                </div>
            `;
        }
        
        // Circuit breaker status (if available)
        if (healthData.circuit_breakers) {
            Object.entries(healthData.circuit_breakers).forEach(([name, cb]) => {
                const cbColor = cb.state === 'closed' ? 'green' : cb.state === 'half_open' ? 'yellow' : 'red';
                html += `
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600">${name.toUpperCase()} Circuit</span>
                        <div class="flex items-center space-x-2">
                            <span class="text-xs text-gray-500">${cb.state}</span>
                            <div class="w-2 h-2 bg-${cbColor}-500 rounded-full"></div>
                        </div>
                    </div>
                `;
            });
        }
        
        panel.innerHTML = html;
        
        // Update header status
        const headerColor = overallStatus === 'healthy' ? 'green' : overallStatus === 'degraded' ? 'yellow' : 'red';
        statusHeader.innerHTML = `
            <div class="flex items-center space-x-1">
                <div class="w-2 h-2 bg-${headerColor}-500 rounded-full"></div>
                <span class="text-sm text-gray-600">${overallStatus}</span>
            </div>
        `;
    }

    // Enhanced WebSocket Message Handlers
    updateConsultationProgress(data) {
        const { consultation_id, step, progress, message, estimated_time } = data;

        if (consultation_id) {
            this.currentConsultationId = consultation_id;
        }

        // Update progress bar
        this.updateProgressBar(progress, message);

        // Update step indicator
        if (step && this.progressSteps.includes(step)) {
            this.currentStep = this.progressSteps.indexOf(step);
            this.updateStepIndicator(this.currentStep);
        }

        // Show estimated time remaining
        if (estimated_time) {
            this.updateTimeEstimate(estimated_time);
        }

        // Show progress message
        if (message) {
            this.showProgressMessage(message);
        }
    }

    updateProgressBar(progress, message) {
        const progressBar = document.getElementById('consultation-progress');
        const progressText = document.getElementById('progress-text');

        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }

        if (progressText && message) {
            progressText.textContent = message;
        }
    }

    updateStepIndicator(currentStep) {
        const stepIndicators = document.querySelectorAll('.step-indicator');

        stepIndicators.forEach((indicator, index) => {
            indicator.classList.remove('active', 'completed');

            if (index < currentStep) {
                indicator.classList.add('completed');
            } else if (index === currentStep) {
                indicator.classList.add('active');
            }
        });
    }

    updateTimeEstimate(estimatedTime) {
        const timeElement = document.getElementById('estimated-time');
        if (timeElement) {
            timeElement.textContent = `Estimated time: ${estimatedTime}`;
        }
    }

    showProgressMessage(message) {
        const messageElement = document.getElementById('progress-message');
        if (messageElement) {
            messageElement.textContent = message;
            messageElement.classList.add('fade-in');

            // Remove fade-in class after animation
            setTimeout(() => {
                messageElement.classList.remove('fade-in');
            }, 500);
        }
    }

    updateConnectionStatus(status) {
        this.connectionStatus = status;

        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.className = `connection-status status-${status}`;
            statusIndicator.textContent = this.getStatusText(status);
        }

        // Update UI based on connection status
        this.updateUIForConnectionStatus(status);
    }

    getStatusText(status) {
        const statusTexts = {
            'connected': 'Connected',
            'disconnected': 'Disconnected',
            'error': 'Connection Error',
            'failed': 'Connection Failed'
        };
        return statusTexts[status] || 'Unknown';
    }

    updateUIForConnectionStatus(status) {
        const isConnected = status === 'connected';

        // Enable/disable real-time features
        const realtimeElements = document.querySelectorAll('[data-requires-connection]');
        realtimeElements.forEach(element => {
            element.disabled = !isConnected;
            if (!isConnected) {
                element.title = 'Requires active connection';
            }
        });
    }

    // Audio Recording
    async setupAudioVisualization() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
        } catch (error) {
            console.warn('Audio visualization not available:', error);
        }
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            this.audioChunks = [];
            
            // Setup audio visualization
            if (this.audioContext && this.analyser) {
                this.microphone = this.audioContext.createMediaStreamSource(stream);
                this.microphone.connect(this.analyser);
                this.visualizeAudio();
            }
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.submitVoiceConsultation(audioBlob);
                
                // Stop audio visualization
                if (this.microphone) {
                    this.microphone.disconnect();
                    this.microphone = null;
                }
            };
            
            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            
            this.updateRecordingUI(true);
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.showError('Could not access microphone. Please check permissions.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            this.isRecording = false;
            
            this.updateRecordingUI(false);
        }
    }
    
    visualizeAudio() {
        if (!this.isRecording || !this.analyser) return;
        
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.analyser.getByteFrequencyData(dataArray);
        
        // Calculate average volume
        const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
        const percentage = (average / 255) * 100;
        
        // Update audio level indicator
        const audioLevel = document.getElementById('audio-level');
        if (audioLevel) {
            audioLevel.style.width = `${percentage}%`;
        }
        
        // Continue visualization
        if (this.isRecording) {
            requestAnimationFrame(() => this.visualizeAudio());
        }
    }
    
    updateRecordingUI(recording) {
        const recordBtn = document.getElementById('record-btn');
        const recordingStatus = document.getElementById('recording-status');
        const audioLevel = document.getElementById('audio-level');
        
        if (recording) {
            recordBtn.classList.add('recording', 'bg-red-600');
            recordBtn.classList.remove('bg-red-500');
            recordingStatus.textContent = 'Recording... Click to stop';
        } else {
            recordBtn.classList.remove('recording', 'bg-red-600');
            recordBtn.classList.add('bg-red-500');
            recordingStatus.textContent = 'Processing...';
            if (audioLevel) {
                audioLevel.style.width = '0%';
            }
        }
    }
    
    async submitVoiceConsultation(audioBlob) {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.webm');
        
        // Add patient demographics if filled
        const age = document.getElementById('patient_age')?.value;
        const gender = document.getElementById('patient_gender')?.value;
        const history = document.getElementById('medical_history')?.value;
        
        if (age) formData.append('patient_age', age);
        if (gender) formData.append('patient_gender', gender);
        if (history) formData.append('medical_history', history);
        
        try {
            const response = await fetch('/api/consultation/voice', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('Error submitting voice consultation:', error);
            this.showError('Error processing audio. Please try again.');
        } finally {
            const recordingStatus = document.getElementById('recording-status');
            if (recordingStatus) {
                recordingStatus.textContent = 'Click to start recording';
            }
        }
    }
    
    displayResults(result) {
        const panel = document.getElementById('results-panel');
        if (!panel) return;
        
        if (result.success) {
            const analysis = result.analysis;
            const urgencyClass = `urgency-${analysis.urgency}`;
            
            let html = `
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-lg font-semibold text-gray-900">Analysis Results</h3>
                        <span class="px-3 py-1 rounded-full text-sm font-medium border ${urgencyClass}">
                            ${analysis.urgency.toUpperCase()}
                        </span>
                    </div>
            `;
            
            if (result.transcription) {
                html += `
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h4 class="font-medium text-gray-900 mb-2">Transcription</h4>
                        <p class="text-gray-700">${this.escapeHtml(result.transcription)}</p>
                    </div>
                `;
            }
            
            html += `
                <div class="bg-blue-50 rounded-lg p-4">
                    <h4 class="font-medium text-gray-900 mb-2">Medical Response</h4>
                    <p class="text-gray-700">${this.escapeHtml(analysis.patient_friendly_response)}</p>
                </div>
            `;
            
            if (analysis.recommendations && analysis.recommendations.length > 0) {
                html += `
                    <div>
                        <h4 class="font-medium text-gray-900 mb-2">Recommendations</h4>
                        <ul class="list-disc list-inside space-y-1">
                `;
                analysis.recommendations.forEach(rec => {
                    html += `<li class="text-gray-700">${this.escapeHtml(rec)}</li>`;
                });
                html += `</ul></div>`;
            }
            
            if (analysis.red_flags && analysis.red_flags.length > 0) {
                html += `
                    <div class="bg-red-50 rounded-lg p-4">
                        <h4 class="font-medium text-red-900 mb-2">⚠️ Important Warnings</h4>
                        <ul class="list-disc list-inside space-y-1">
                `;
                analysis.red_flags.forEach(flag => {
                    html += `<li class="text-red-700">${this.escapeHtml(flag)}</li>`;
                });
                html += `</ul></div>`;
            }
            
            html += `
                <div class="text-xs text-gray-500 pt-4 border-t">
                    Model: ${this.escapeHtml(analysis.model_used)} | 
                    Confidence: ${(analysis.confidence * 100).toFixed(1)}%
                    ${result.processing_time_ms ? ` | Processing: ${result.processing_time_ms}ms` : ''}
                    ${result.consultation_id ? ` | ID: ${result.consultation_id.slice(0, 8)}...` : ''}
                </div>
            </div>
            `;
            
            panel.innerHTML = html;
        } else {
            this.showError('Analysis failed. Please try again.');
        }
    }
    
    showError(message) {
        const panel = document.getElementById('results-panel');
        if (panel) {
            panel.innerHTML = `
                <div class="text-center text-red-600 py-8">
                    <div class="text-4xl mb-4">❌</div>
                    <p>${this.escapeHtml(message)}</p>
                </div>
            `;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    setupEventListeners() {
        // Record button
        const recordBtn = document.getElementById('record-btn');
        if (recordBtn) {
            recordBtn.addEventListener('click', () => {
                if (!this.isRecording) {
                    this.startRecording();
                } else {
                    this.stopRecording();
                }
            });
        }
        
        // File upload
        const audioFile = document.getElementById('audio-file');
        if (audioFile) {
            audioFile.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    await this.submitVoiceConsultation(file);
                }
            });
        }
        
        // HTMX response handler for text consultations
        document.body.addEventListener('htmx:afterRequest', (evt) => {
            if (evt.detail.xhr.status === 200 && evt.detail.target.id === 'results-panel') {
                try {
                    const result = JSON.parse(evt.detail.xhr.responseText);
                    this.displayResults(result);
                } catch (e) {
                    console.error('Error parsing response:', e);
                    this.showError('Error parsing server response');
                }
            }
        });
        
        // Handle HTMX errors
        document.body.addEventListener('htmx:responseError', (evt) => {
            console.error('HTMX response error:', evt.detail);
            this.showError('Server error occurred. Please try again.');
        });
        
        document.body.addEventListener('htmx:sendError', (evt) => {
            console.error('HTMX send error:', evt.detail);
            this.showError('Network error occurred. Please check your connection.');
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.medicalApp = new MedicalResearchApp();
});

// Global function for backward compatibility
function toggleRecording() {
    if (window.medicalApp) {
        if (!window.medicalApp.isRecording) {
            window.medicalApp.startRecording();
        } else {
            window.medicalApp.stopRecording();
        }
    }
}
