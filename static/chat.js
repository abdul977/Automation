// Enhanced WhatsApp Bot Chat Interface JavaScript

class WhatsAppChat {
    constructor() {
        this.contacts = JSON.parse(localStorage.getItem('whatsapp_contacts') || '[]');
        this.activeContact = null;
        this.messageHistory = JSON.parse(localStorage.getItem('whatsapp_messages') || '{}');
        
        this.initializeElements();
        this.loadContacts();
        this.setupEventListeners();
        this.checkBotStatus();
        
        // Check bot status every 30 seconds
        setInterval(() => this.checkBotStatus(), 30000);
    }

    initializeElements() {
        this.contactsList = document.getElementById('contactsList');
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatTitle = document.getElementById('chatTitle');
        this.chatStatus = document.getElementById('chatStatus');
        this.chatInputContainer = document.getElementById('chatInputContainer');
        this.addContactModal = document.getElementById('addContactModal');
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // Close modal when clicking outside
        this.addContactModal.addEventListener('click', (e) => {
            if (e.target === this.addContactModal) {
                this.hideAddContactModal();
            }
        });
    }

    loadContacts() {
        this.contactsList.innerHTML = '';
        
        if (this.contacts.length === 0) {
            this.contactsList.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No contacts yet. Add your first contact!</div>';
            return;
        }

        this.contacts.forEach(contact => {
            const contactElement = document.createElement('div');
            contactElement.className = 'contact-item';
            contactElement.innerHTML = `
                <div class="contact-name">${contact.name}</div>
                <div class="contact-phone">${contact.phone}</div>
            `;
            
            contactElement.addEventListener('click', () => this.selectContact(contact));
            this.contactsList.appendChild(contactElement);
        });
    }

    selectContact(contact) {
        this.activeContact = contact;
        
        // Update UI
        document.querySelectorAll('.contact-item').forEach(item => {
            item.classList.remove('active');
        });
        
        event.currentTarget.classList.add('active');
        
        this.chatTitle.textContent = contact.name;
        this.chatStatus.textContent = `📱 ${contact.phone}`;
        this.chatInputContainer.style.display = 'flex';
        
        // Load message history
        this.loadMessageHistory(contact.phone);
        this.messageInput.focus();
    }

    loadMessageHistory(phone) {
        const messages = this.messageHistory[phone] || [];
        this.chatMessages.innerHTML = '';
        
        if (messages.length === 0) {
            this.addSystemMessage(`Start chatting with ${this.activeContact.name}! 💬`);
            return;
        }

        messages.forEach(msg => {
            this.addMessage(msg.text, msg.type, msg.timestamp);
        });
    }

    addMessage(text, type, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) 
                                  : new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div>${this.escapeHtml(text)}</div>
            <div class="message-time">${timeStr}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // Save to history
        if (this.activeContact) {
            this.saveMessageToHistory(text, type, timestamp);
        }
    }

    addSystemMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message received';
        messageDiv.style.background = '#e3f2fd';
        messageDiv.style.borderColor = '#2196f3';
        
        messageDiv.innerHTML = `
            <div>🤖 ${this.escapeHtml(text)}</div>
            <div class="message-time">System</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    saveMessageToHistory(text, type, timestamp = null) {
        if (!this.activeContact) return;
        
        const phone = this.activeContact.phone;
        if (!this.messageHistory[phone]) {
            this.messageHistory[phone] = [];
        }
        
        this.messageHistory[phone].push({
            text: text,
            type: type,
            timestamp: timestamp || Date.now()
        });
        
        // Keep only last 100 messages per contact
        if (this.messageHistory[phone].length > 100) {
            this.messageHistory[phone] = this.messageHistory[phone].slice(-100);
        }
        
        localStorage.setItem('whatsapp_messages', JSON.stringify(this.messageHistory));
    }

    async sendMessage() {
        if (!this.activeContact) {
            this.showNotification('Please select a contact first', 'error');
            return;
        }

        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add sent message to chat
        this.addMessage(message, 'sent');
        this.messageInput.value = '';
        
        // Disable send button and show loading
        this.sendButton.disabled = true;
        this.sendButton.textContent = 'Sending...';

        try {
            const response = await fetch('/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    to: this.activeContact.phone,
                    message: message
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Message sent successfully!', 'success');
            } else {
                this.showNotification(`Failed to send: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Network error: ${error.message}`, 'error');
        } finally {
            this.sendButton.disabled = false;
            this.sendButton.textContent = 'Send';
        }
    }

    showAddContactModal() {
        this.addContactModal.style.display = 'block';
        document.getElementById('contactName').focus();
    }

    hideAddContactModal() {
        this.addContactModal.style.display = 'none';
        document.getElementById('contactName').value = '';
        document.getElementById('contactPhone').value = '';
    }

    addContact() {
        const name = document.getElementById('contactName').value.trim();
        const phone = document.getElementById('contactPhone').value.trim();
        
        if (!name || !phone) {
            this.showNotification('Please enter both name and phone number', 'error');
            return;
        }

        // Validate phone number
        if (!/^\d{10,15}$/.test(phone)) {
            this.showNotification('Please enter a valid phone number (10-15 digits)', 'error');
            return;
        }

        // Check if contact already exists
        if (this.contacts.find(c => c.phone === phone)) {
            this.showNotification('Contact with this phone number already exists', 'error');
            return;
        }

        // Add contact
        const newContact = { name, phone };
        this.contacts.push(newContact);
        localStorage.setItem('whatsapp_contacts', JSON.stringify(this.contacts));
        
        this.loadContacts();
        this.hideAddContactModal();
        this.showNotification(`Contact ${name} added successfully!`, 'success');
    }

    clearChat() {
        if (!this.activeContact) return;
        
        if (confirm(`Clear chat history with ${this.activeContact.name}?`)) {
            delete this.messageHistory[this.activeContact.phone];
            localStorage.setItem('whatsapp_messages', JSON.stringify(this.messageHistory));
            this.loadMessageHistory(this.activeContact.phone);
            this.showNotification('Chat history cleared', 'info');
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('mobile-show');
    }

    async checkBotStatus() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                this.chatStatus.style.color = '#25D366';
            } else {
                this.chatStatus.style.color = '#dc3545';
            }
        } catch (error) {
            this.chatStatus.style.color = '#dc3545';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for HTML onclick events
function showAddContactModal() {
    window.chatApp.showAddContactModal();
}

function hideAddContactModal() {
    window.chatApp.hideAddContactModal();
}

function addContact() {
    window.chatApp.addContact();
}

function clearChat() {
    window.chatApp.clearChat();
}

function toggleSidebar() {
    window.chatApp.toggleSidebar();
}

// Initialize the chat application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new WhatsAppChat();
});
