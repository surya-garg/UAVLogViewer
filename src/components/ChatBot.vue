<!-- eslint-disable -->
<template>
    <div class="chatbot-container" :class="{ 'minimized': isMinimized }">
        <!-- Chat Header -->
        <div class="chat-header" @click="toggleMinimize">
            <div class="header-content">
                <div class="header-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                <div class="header-title">
                    <h3>Flight Analysis Assistant</h3>
                    <span class="status-indicator" :class="{ 'connected': hasLog }">
                        {{ hasLog ? 'Log Loaded' : 'No Log Loaded' }}
                    </span>
                </div>
            </div>
            <button class="minimize-btn" @click.stop="toggleMinimize">
                <svg v-if="!isMinimized" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
            </button>
        </div>

        <!-- Chat Body -->
        <div v-if="!isMinimized" class="chat-body">
            <!-- Welcome Message -->
            <div v-if="messages.length === 0" class="welcome-message">
                <div class="welcome-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                        <path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path>
                    </svg>
                </div>
                <h4>Welcome to Flight Analysis Assistant</h4>
                <p v-if="!hasLog">Upload a .bin file to start analyzing your flight data</p>
                <p v-else>Ask me anything about your flight!</p>
                <div class="example-questions">
                    <p class="example-title">Example questions:</p>
                    <button v-for="(q, idx) in exampleQuestions" :key="idx"
                            class="example-btn" @click="sendMessage(q)">
                        {{ q }}
                    </button>
                </div>
            </div>

            <!-- Messages -->
            <div class="messages-container" ref="messagesContainer">
                <div v-for="(msg, idx) in messages" :key="idx"
                     class="message" :class="msg.role">
                    <div class="message-avatar">
                        <svg v-if="msg.role === 'user'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                            <path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path>
                        </svg>
                    </div>
                    <div class="message-content">
                        <div class="message-text" v-html="formatMessage(msg.content)"></div>
                        <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
                    </div>
                </div>

                <!-- Typing Indicator -->
                <div v-if="isTyping" class="message assistant">
                    <div class="message-avatar">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                            <path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path>
                        </svg>
                    </div>
                    <div class="message-content">
                        <div class="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Input Area -->
            <div class="chat-input-container">
                <textarea
                    v-model="inputMessage"
                    @keydown.enter.exact.prevent="handleSend"
                    @keydown.enter.shift.exact="inputMessage += '\n'"
                    placeholder="Ask about your flight data..."
                    :disabled="!hasLog || isTyping"
                    rows="1"
                    ref="inputField"
                ></textarea>
                <button
                    @click="handleSend"
                    :disabled="!inputMessage.trim() || !hasLog || isTyping"
                    class="send-btn"
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>

            <!-- Quick Actions -->
            <div class="quick-actions" v-if="hasLog && messages.length > 0">
                <button @click="resetConversation" class="action-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="1 4 1 10 7 10"></polyline>
                        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
                    </svg>
                    Reset Chat
                </button>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios'

export default {
    name: 'ChatBot',
    props: {
        sessionId: {
            type: String,
            default: null
        },
        hasLog: {
            type: Boolean,
            default: false
        }
    },
    data () {
        return {
            isMinimized: false,
            messages: [],
            inputMessage: '',
            isTyping: false,
            apiBaseUrl: 'http://localhost:8000/api',
            exampleQuestions: [
                'What was the maximum altitude?',
                'Are there any anomalies in this flight?',
                'How long was the flight?',
                'Were there any GPS issues?'
            ]
        }
    },
    methods: {
        toggleMinimize () {
            this.isMinimized = !this.isMinimized
        },

        async sendMessage (message = null) {
            const msg = message || this.inputMessage.trim()
            if (!msg || !this.hasLog) return

            // Add user message
            this.messages.push({
                role: 'user',
                content: msg,
                timestamp: new Date()
            })

            this.inputMessage = ''
            this.isTyping = true
            this.scrollToBottom()

            try {
                const response = await axios.post(`${this.apiBaseUrl}/chat`, {
                    session_id: this.sessionId, // eslint-disable-line camelcase
                    message: msg
                })

                // Add assistant response
                this.messages.push({
                    role: 'assistant',
                    content: response.data.message,
                    timestamp: new Date(response.data.timestamp)
                })
            } catch (error) {
                console.error('Chat error:', error)
                this.messages.push({
                    role: 'assistant',
                    content: 'Sorry, I encountered an error. Please try again.',
                    timestamp: new Date()
                })
            } finally {
                this.isTyping = false
                this.scrollToBottom()
            }
        },

        handleSend () {
            this.sendMessage()
        },

        async resetConversation () {
            if (!confirm('Are you sure you want to reset the conversation?')) return

            try {
                await axios.post(`${this.apiBaseUrl}/session/${this.sessionId}/reset`)
                this.messages = []
            } catch (error) {
                console.error('Reset error:', error)
            }
        },

        formatMessage (content) {
            // Convert markdown-style formatting to HTML
            const formatted = content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>')

            return formatted
        },

        formatTime (timestamp) {
            const date = new Date(timestamp)
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            })
        },

        scrollToBottom () {
            this.$nextTick(() => {
                const container = this.$refs.messagesContainer
                if (container) {
                    container.scrollTop = container.scrollHeight
                }
            })
        }
    },
    watch: {
        hasLog (newVal) {
            if (newVal && this.messages.length === 0) {
                // Add welcome message when log is loaded
                this.messages.push({
                    role: 'assistant',
                    content: 'Hello! I\'ve analyzed your flight log. What would you like to know?',
                    timestamp: new Date()
                })
                this.scrollToBottom()
            }
        }
    }
}
</script>

<style scoped>
.chatbot-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    max-height: 600px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    z-index: 1000;
    transition: all 0.3s ease;
}

.chatbot-container.minimized {
    max-height: 60px;
}

.chat-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px;
    border-radius: 12px 12px 0 0;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-content {
    display: flex;
    align-items: center;
    gap: 12px;
}

.header-icon {
    display: flex;
    align-items: center;
}

.header-title h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
}

.status-indicator {
    font-size: 12px;
    opacity: 0.8;
}

.status-indicator.connected {
    color: #4ade80;
}

.minimize-btn {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    padding: 4px;
    display: flex;
    align-items: center;
    transition: opacity 0.2s;
}

.minimize-btn:hover {
    opacity: 0.8;
}

.chat-body {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
}

.welcome-message {
    padding: 32px 24px;
    text-align: center;
    color: #64748b;
}

.welcome-icon {
    color: #667eea;
    margin-bottom: 16px;
}

.welcome-message h4 {
    margin: 0 0 8px 0;
    color: #1e293b;
    font-size: 18px;
}

.welcome-message p {
    margin: 0 0 24px 0;
    font-size: 14px;
}

.example-questions {
    text-align: left;
}

.example-title {
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 8px;
}

.example-btn {
    display: block;
    width: 100%;
    text-align: left;
    padding: 10px 12px;
    margin-bottom: 8px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 13px;
    color: #475569;
    cursor: pointer;
    transition: all 0.2s;
}

.example-btn:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
}

.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    max-height: 400px;
}

.message {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}

.message.user {
    flex-direction: row-reverse;
}

.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.message.user .message-avatar {
    background: #667eea;
    color: white;
}

.message.assistant .message-avatar {
    background: #f1f5f9;
    color: #64748b;
}

.message-content {
    max-width: 75%;
}

.message.user .message-content {
    text-align: right;
}

.message-text {
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
}

.message.user .message-text {
    background: #667eea;
    color: white;
    border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
    background: #f8fafc;
    color: #1e293b;
    border-bottom-left-radius: 4px;
}

.message-text >>> strong {
    font-weight: 600;
}

.message-text >>> code {
    background: rgba(0, 0, 0, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 13px;
}

.message-time {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 4px;
}

.typing-indicator {
    display: flex;
    gap: 4px;
    padding: 12px 16px;
    background: #f8fafc;
    border-radius: 12px;
    border-bottom-left-radius: 4px;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #cbd5e1;
    animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% {
        transform: translateY(0);
        opacity: 0.7;
    }
    30% {
        transform: translateY(-10px);
        opacity: 1;
    }
}

.chat-input-container {
    display: flex;
    gap: 8px;
    padding: 16px;
    border-top: 1px solid #e2e8f0;
}

.chat-input-container textarea {
    flex: 1;
    padding: 12px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 14px;
    font-family: inherit;
    resize: none;
    max-height: 100px;
}

.chat-input-container textarea:focus {
    outline: none;
    border-color: #667eea;
}

.chat-input-container textarea:disabled {
    background: #f8fafc;
    cursor: not-allowed;
}

.send-btn {
    width: 40px;
    height: 40px;
    border: none;
    background: #667eea;
    color: white;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
    background: #5568d3;
}

.send-btn:disabled {
    background: #cbd5e1;
    cursor: not-allowed;
}

.quick-actions {
    padding: 8px 16px 16px;
    display: flex;
    gap: 8px;
}

.action-btn {
    padding: 8px 12px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 13px;
    color: #64748b;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
}

.action-btn:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
}

/* Scrollbar styling */
.messages-container::-webkit-scrollbar {
    width: 6px;
}

.messages-container::-webkit-scrollbar-track {
    background: #f1f5f9;
}

.messages-container::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>
