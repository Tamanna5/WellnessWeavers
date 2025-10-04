// WellnessWeavers - Main JavaScript

// Global app object
window.WellnessWeavers = window.WellnessWeavers || {};

// Utility functions
const Utils = {
    // Show toast notifications
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.style.cssText = 'position: relative; margin-bottom: 0.5rem;';
        
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    },

    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        document.body.appendChild(container);
        return container;
    },

    // Format date to readable string
    formatDate: function(date) {
        return new Intl.DateTimeFormat('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },

    // Debounce function calls
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Show loading spinner
    showLoading: function(element) {
        const original = element.innerHTML;
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        element.disabled = true;
        return () => {
            element.innerHTML = original;
            element.disabled = false;
        };
    },

    // API helper
    api: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Something went wrong');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            this.showToast(error.message, 'danger');
            throw error;
        }
    }
};

// Mood tracking functionality
const MoodTracker = {
    currentMood: null,
    
    init: function() {
        this.bindEvents();
    },

    bindEvents: function() {
        // Mood emoji selection
        document.querySelectorAll('.mood-emoji').forEach(emoji => {
            emoji.addEventListener('click', (e) => {
                this.selectMood(e.target);
            });
        });

        // Mood form submission
        const moodForm = document.getElementById('mood-form');
        if (moodForm) {
            moodForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitMood();
            });
        }
    },

    selectMood: function(element) {
        // Remove previous selections
        document.querySelectorAll('.mood-emoji').forEach(emoji => {
            emoji.classList.remove('selected');
        });
        
        // Select current mood
        element.classList.add('selected');
        this.currentMood = element.dataset.mood;
        
        // Show mood form if hidden
        const moodDetails = document.getElementById('mood-details');
        if (moodDetails) {
            moodDetails.style.display = 'block';
        }
    },

    submitMood: async function() {
        if (!this.currentMood) {
            Utils.showToast('Please select a mood first', 'warning');
            return;
        }

        const form = document.getElementById('mood-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        data.mood = this.currentMood;

        try {
            await Utils.api('/api/mood', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            Utils.showToast('Mood recorded successfully!', 'success');
            form.reset();
            this.currentMood = null;
            
            // Hide mood details
            const moodDetails = document.getElementById('mood-details');
            if (moodDetails) {
                moodDetails.style.display = 'none';
            }
            
            // Clear selections
            document.querySelectorAll('.mood-emoji').forEach(emoji => {
                emoji.classList.remove('selected');
            });
            
        } catch (error) {
            Utils.showToast('Failed to record mood', 'danger');
        }
    }
};

// Chat functionality
const Chat = {
    init: function() {
        this.bindEvents();
        this.loadRecentMessages();
    },

    bindEvents: function() {
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }
    },

    loadRecentMessages: function() {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        // Placeholder for loading recent messages
        this.addMessage('ai', 'Hello! I\'m here to support you. How are you feeling today?');
    },

    addMessage: function(sender, text) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-time">${Utils.formatDate(new Date())}</div>
        `;
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    },

    sendMessage: async function() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message);
        input.value = '';

        try {
            const response = await Utils.api('/api/chat', {
                method: 'POST',
                body: JSON.stringify({ message })
            });
            
            // Add AI response
            this.addMessage('ai', response.response);
            
        } catch (error) {
            this.addMessage('ai', 'I\'m sorry, I\'m having trouble responding right now. Please try again later.');
        }
    }
};

// Voice recording functionality
const VoiceRecorder = {
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,

    init: function() {
        this.bindEvents();
    },

    bindEvents: function() {
        const recordBtn = document.getElementById('record-btn');
        if (recordBtn) {
            recordBtn.addEventListener('click', () => {
                this.toggleRecording();
            });
        }
    },

    toggleRecording: async function() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    },

    startRecording: async function() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.processAudio(audioBlob);
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            
            const recordBtn = document.getElementById('record-btn');
            recordBtn.classList.add('recording');
            recordBtn.innerHTML = '<i class="fas fa-stop"></i>';
            
            Utils.showToast('Recording started...', 'info');
            
        } catch (error) {
            Utils.showToast('Unable to access microphone', 'danger');
        }
    },

    stopRecording: function() {
        if (this.mediaRecorder) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        this.isRecording = false;
        
        const recordBtn = document.getElementById('record-btn');
        recordBtn.classList.remove('recording');
        recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        
        Utils.showToast('Recording stopped, processing...', 'info');
    },

    processAudio: async function(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        try {
            const response = await fetch('/api/voice-journal', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            Utils.showToast('Voice journal entry saved!', 'success');
            
            // Display transcription if available
            if (data.transcription) {
                const transcriptionDiv = document.getElementById('transcription');
                if (transcriptionDiv) {
                    transcriptionDiv.innerHTML = `<strong>Transcription:</strong> ${data.transcription}`;
                }
            }
            
        } catch (error) {
            Utils.showToast('Failed to process audio', 'danger');
        }
    }
};

// Form validation
const FormValidator = {
    init: function() {
        this.bindEvents();
    },

    bindEvents: function() {
        // Real-time validation
        document.querySelectorAll('input[required], textarea[required]').forEach(input => {
            input.addEventListener('blur', (e) => {
                this.validateField(e.target);
            });
        });
    },

    validateField: function(field) {
        const isValid = field.checkValidity();
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            
            if (feedback) {
                feedback.textContent = field.validationMessage;
            }
        }
        
        return isValid;
    },

    validateForm: function(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('input[required], textarea[required]');
        
        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modules
    MoodTracker.init();
    Chat.init();
    VoiceRecorder.init();
    FormValidator.init();

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert-dismissible').forEach(alert => {
            if (alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add fade-in animation to cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .dashboard-card').forEach(card => {
        observer.observe(card);
    });

    console.log('WellnessWeavers application initialized successfully!');
});