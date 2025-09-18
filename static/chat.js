// Enhanced WhatsApp Bot Chat Interface JavaScript

class WhatsAppChat {
    constructor() {
        console.log('🚀 [ENHANCED CHAT] Initializing Enhanced Chat Interface...');

        this.contacts = JSON.parse(localStorage.getItem('whatsapp_contacts') || '[]');
        this.activeContact = null;
        this.messageHistory = {};

        console.log('📱 [ENHANCED CHAT] Loaded contacts from localStorage:', this.contacts);

        this.initializeElements();
        console.log('🔧 [ENHANCED CHAT] Elements initialized');

        this.loadContactsFromServer();
        console.log('🔄 [ENHANCED CHAT] Loading contacts from server...');

        this.setupEventListeners();
        console.log('👂 [ENHANCED CHAT] Event listeners set up');

        this.checkBotStatus();
        console.log('🤖 [ENHANCED CHAT] Checking bot status...');

        // Check bot status every 30 seconds
        setInterval(() => {
            console.log('⏰ [ENHANCED CHAT] Periodic bot status check...');
            this.checkBotStatus();
        }, 30000);

        // Initialize WebSocket for real-time updates
        this.initializeWebSocket();
        console.log('🔌 [ENHANCED CHAT] WebSocket initialized');

        console.log('✅ [ENHANCED CHAT] Enhanced Chat Interface initialized successfully!');
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

    normalizePhoneNumber(phoneNumber) {
        // Remove + prefix and any non-digit characters for consistent comparison
        if (!phoneNumber) return phoneNumber;
        return phoneNumber.replace(/[^\d]/g, '');
    }

    initializeWebSocket() {
        console.log('🔌 [ENHANCED CHAT] Connecting to WebSocket...');

        // Initialize Socket.IO connection
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('✅ [ENHANCED CHAT] WebSocket connected successfully!');

            // Join room for active contact if any
            if (this.activeContact) {
                this.socket.emit('join_room', { phone_number: this.activeContact.phone });
            }
        });

        this.socket.on('disconnect', () => {
            console.log('❌ [ENHANCED CHAT] WebSocket disconnected');
        });

        this.socket.on('new_message', (data) => {
            console.log('📨 [ENHANCED CHAT] Received real-time message:', data);
            this.handleNewMessage(data);
        });

        this.socket.on('connect_error', (error) => {
            console.error('💥 [ENHANCED CHAT] WebSocket connection error:', error);
        });
    }

    handleNewMessage(data) {
        const { phone_number, message } = data;
        console.log(`📱 [ENHANCED CHAT] New message for ${phone_number}:`, message);

        // Update message history
        if (!this.messageHistory[phone_number]) {
            this.messageHistory[phone_number] = [];
        }
        this.messageHistory[phone_number].push(message);

        // If this is the active contact, update the chat display
        if (this.activeContact) {
            const activePhoneNormalized = this.normalizePhoneNumber(this.activeContact.phone);
            console.log(`🔍 [ENHANCED CHAT] Checking if message is for active contact:`);
            console.log(`   Active contact phone: ${this.activeContact.phone}`);
            console.log(`   Active normalized: ${activePhoneNormalized}`);
            console.log(`   Message phone: ${phone_number}`);
            console.log(`   Match: ${activePhoneNormalized === phone_number}`);

            if (activePhoneNormalized === phone_number) {
                console.log(`✅ [ENHANCED CHAT] Message is for active contact, updating display`);
                this.displayMessages();
            }
        } else {
            console.log(`ℹ️ [ENHANCED CHAT] No active contact selected`);
        }

        // Update contact list to show new message
        this.updateContactInList(phone_number, message);
    }

    updateContactInList(phone_number, message) {
        console.log(`📋 [ENHANCED CHAT] Updating contact list for ${phone_number} with new message`);

        // Find or create contact in the list
        let contact = this.contacts.find(c => this.normalizePhoneNumber(c.phone) === phone_number);

        if (!contact) {
            // Create new contact if not exists
            contact = {
                name: `+${phone_number}`,
                phone: `+${phone_number}`,
                lastMessage: message.text,
                lastMessageTime: message.timestamp,
                messageCount: 1
            };
            this.contacts.unshift(contact); // Add to beginning of list
            console.log(`➕ [ENHANCED CHAT] Created new contact for ${phone_number}`);
        } else {
            // Update existing contact
            contact.lastMessage = message.text;
            contact.lastMessageTime = message.timestamp;
            contact.messageCount = (contact.messageCount || 0) + 1;
            console.log(`🔄 [ENHANCED CHAT] Updated existing contact for ${phone_number}`);
        }

        // Save to localStorage
        localStorage.setItem('whatsapp_contacts', JSON.stringify(this.contacts));

        // Refresh the contact list display
        this.displayContacts();

        console.log(`✅ [ENHANCED CHAT] Contact list updated for ${phone_number}`);
    }

    updateContactInList(phone_number, message) {
        // Find and update the contact in the list to show the latest message
        const contactItems = document.querySelectorAll('.contact-item');
        contactItems.forEach(item => {
            const contactPhone = item.dataset.phone;
            if (this.normalizePhoneNumber(contactPhone) === this.normalizePhoneNumber(phone_number)) {
                // Update last message preview
                const lastMessageElement = item.querySelector('.contact-last-message');
                if (lastMessageElement) {
                    const preview = message.text.length > 30 ? message.text.substring(0, 30) + '...' : message.text;
                    lastMessageElement.textContent = preview;
                }

                // Update message count if available
                const messageCountElement = item.querySelector('.contact-message-count');
                if (messageCountElement && this.messageHistory[phone_number]) {
                    messageCountElement.textContent = this.messageHistory[phone_number].length;
                }
            }
        });
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

            const lastMessageInfo = contact.lastMessage ?
                `<div class="contact-last-message">${contact.lastMessage}</div>
                 <div class="contact-message-count">${contact.messageCount || 0} messages</div>` :
                '<div class="contact-last-message">No messages yet</div>';

            contactElement.innerHTML = `
                <div class="contact-name">${contact.name}</div>
                <div class="contact-phone">${contact.phone}</div>
                ${lastMessageInfo}
            `;

            contactElement.addEventListener('click', () => this.selectContact(contact));
            this.contactsList.appendChild(contactElement);
        });
    }

    async loadContactsFromServer() {
        try {
            console.log('🔄 [ENHANCED CHAT] Loading contacts from server...');
            const response = await fetch('/api/contacts');
            const data = await response.json();

            console.log('📋 [ENHANCED CHAT] Server response for contacts:', data);

            if (data.status === 'success') {
                console.log(`✅ [ENHANCED CHAT] Found ${data.contacts.length} contacts on server`);

                // Merge server contacts with local contacts
                const serverContacts = data.contacts.map(contact => ({
                    name: contact.display_name,
                    phone: `+${contact.phone_number}`,
                    lastMessage: contact.last_message,
                    lastMessageTime: contact.last_message_time,
                    messageCount: contact.message_count
                }));

                console.log('🔄 [ENHANCED CHAT] Mapped server contacts:', serverContacts);

                // Add any local contacts that aren't on server
                const localContacts = JSON.parse(localStorage.getItem('whatsapp_contacts') || '[]');
                console.log('📱 [ENHANCED CHAT] Local contacts from localStorage:', localContacts);

                localContacts.forEach(localContact => {
                    if (!serverContacts.find(sc => sc.phone === localContact.phone)) {
                        console.log(`➕ [ENHANCED CHAT] Adding local contact not on server:`, localContact);
                        serverContacts.push(localContact);
                    }
                });

                this.contacts = serverContacts;
                console.log('📋 [ENHANCED CHAT] Final merged contacts:', this.contacts);
                this.loadContacts();
            } else {
                console.error('❌ [ENHANCED CHAT] Server returned error:', data);
            }
        } catch (error) {
            console.error('💥 [ENHANCED CHAT] Error loading contacts from server:', error);
            // Fall back to local storage
            console.log('🔄 [ENHANCED CHAT] Falling back to local storage...');
            this.loadContacts();
        }
    }

    async loadMessagesForContact(phoneNumber) {
        try {
            console.log(`💬 [ENHANCED CHAT] Loading messages for contact: ${phoneNumber}`);

            // Remove + prefix for API call
            const normalizedPhone = phoneNumber.replace('+', '');
            console.log(`🔄 [ENHANCED CHAT] Normalized phone for API: ${normalizedPhone}`);

            const response = await fetch(`/api/messages/${normalizedPhone}`);
            const data = await response.json();

            console.log(`📨 [ENHANCED CHAT] Server response for messages (${normalizedPhone}):`, data);

            if (data.status === 'success') {
                console.log(`✅ [ENHANCED CHAT] Found ${data.messages.length} messages for ${phoneNumber}`);
                this.messageHistory[phoneNumber] = data.messages;
                console.log(`📋 [ENHANCED CHAT] Updated message history for ${phoneNumber}:`, data.messages);
                this.displayMessages();
            } else {
                console.error(`❌ [ENHANCED CHAT] Server returned error for ${phoneNumber}:`, data);
            }
        } catch (error) {
            console.error(`💥 [ENHANCED CHAT] Error loading messages for ${phoneNumber}:`, error);
            // Fall back to local storage
            console.log(`🔄 [ENHANCED CHAT] Falling back to localStorage for ${phoneNumber}...`);
            const localMessages = JSON.parse(localStorage.getItem('whatsapp_messages') || '{}');
            this.messageHistory[phoneNumber] = localMessages[phoneNumber] || [];
            console.log(`📱 [ENHANCED CHAT] Local messages for ${phoneNumber}:`, this.messageHistory[phoneNumber]);
            this.displayMessages();
        }
    }

    // Removed refreshMessages - using WebSocket real-time updates instead

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
        
        // Load message history from server
        this.loadMessagesForContact(contact.phone);
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

    displayMessages() {
        if (!this.activeContact) return;

        const messages = this.messageHistory[this.activeContact.phone] || [];
        this.chatMessages.innerHTML = '';

        if (messages.length === 0) {
            this.addSystemMessage(`Start chatting with ${this.activeContact.name}! 💬`);
            return;
        }

        messages.forEach(msg => {
            this.addMessageFromServer(msg);
        });
    }

    addMessageFromServer(messageData) {
        const messageDiv = document.createElement('div');
        const messageType = messageData.type === 'incoming' ? 'received' : 'sent';
        messageDiv.className = `message ${messageType}`;

        const timeStr = new Date(messageData.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        messageDiv.innerHTML = `
            <div>${this.escapeHtml(messageData.text)}</div>
            <div class="message-time">${timeStr}</div>
        `;

        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
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
            console.warn('⚠️ [ENHANCED CHAT] No active contact selected');
            this.showNotification('Please select a contact first', 'error');
            return;
        }

        const message = this.messageInput.value.trim();
        if (!message) {
            console.warn('⚠️ [ENHANCED CHAT] Empty message, not sending');
            return;
        }

        console.log(`📤 [ENHANCED CHAT] Sending message to ${this.activeContact.phone}: "${message}"`);

        // Add sent message to chat
        this.addMessage(message, 'sent');
        this.messageInput.value = '';

        // Disable send button and show loading
        this.sendButton.disabled = true;
        this.sendButton.textContent = 'Sending...';

        const payload = {
            to: this.activeContact.phone,
            message: message
        };
        console.log('📋 [ENHANCED CHAT] Send payload:', payload);

        try {
            const response = await fetch('/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            console.log(`📨 [ENHANCED CHAT] Send response (${response.status}):`, result);

            if (response.ok) {
                console.log('✅ [ENHANCED CHAT] Message sent successfully!');
                this.showNotification('Message sent successfully!', 'success');
                // Refresh messages to show the sent message from server
                console.log('🔄 [ENHANCED CHAT] Refreshing messages after send...');
                setTimeout(() => this.loadMessagesForContact(this.activeContact.phone), 1000);
            } else {
                console.error('❌ [ENHANCED CHAT] Failed to send message:', result);
                this.showNotification(`Failed to send: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('💥 [ENHANCED CHAT] Network error sending message:', error);
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
        if (!/^\d{10,19}$/.test(phone)) {
            this.showNotification('Please enter a valid phone number (10-19 digits)', 'error');
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
