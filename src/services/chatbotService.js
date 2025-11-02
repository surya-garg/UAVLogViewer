/* eslint-disable camelcase */
/**
 * Chatbot API service for communicating with the backend
 */
import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_CHATBOT_API_URL || 'http://localhost:8000/api'

class ChatbotService {
    constructor () {
        this.sessionId = null
        this.hasLog = false
    }

    /**
     * Upload a .bin file to the chatbot backend
     * @param {File} file - The .bin file to upload
     * @returns {Promise<Object>} Upload response with session_id
     */
    async uploadLog (file) {
        const formData = new FormData()
        formData.append('file', file)

        if (this.sessionId) {
            formData.append('session_id', this.sessionId)
        }

        try {
            const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                    console.log(`Upload progress: ${percentCompleted}%`)
                }
            })

            this.sessionId = response.data.session_id
            this.hasLog = true

            return response.data
        } catch (error) {
            console.error('Upload error:', error)
            throw error
        }
    }

    /**
     * Send a chat message to the agent
     * @param {string} message - The user's message
     * @returns {Promise<Object>} Chat response
     */
    async sendMessage (message) {
        if (!this.sessionId) {
            throw new Error('No active session. Please upload a log file first.')
        }

        try {
            const response = await axios.post(`${API_BASE_URL}/chat`, {
                session_id: this.sessionId, // eslint-disable-line camelcase
                message: message
            })

            return response.data
        } catch (error) {
            console.error('Chat error:', error)
            throw error
        }
    }

    /**
     * Get session information
     * @returns {Promise<Object>} Session info
     */
    async getSessionInfo () {
        if (!this.sessionId) {
            return null
        }

        try {
            const response = await axios.get(`${API_BASE_URL}/session/${this.sessionId}`)
            return response.data
        } catch (error) {
            console.error('Get session error:', error)
            throw error
        }
    }

    /**
     * Reset the conversation history
     * @returns {Promise<Object>} Reset response
     */
    async resetConversation () {
        if (!this.sessionId) {
            throw new Error('No active session')
        }

        try {
            const response = await axios.post(`${API_BASE_URL}/session/${this.sessionId}/reset`)
            return response.data
        } catch (error) {
            console.error('Reset error:', error)
            throw error
        }
    }

    /**
     * Delete the current session
     * @returns {Promise<Object>} Delete response
     */
    async deleteSession () {
        if (!this.sessionId) {
            return
        }

        try {
            const response = await axios.delete(`${API_BASE_URL}/session/${this.sessionId}`)
            this.sessionId = null
            this.hasLog = false
            return response.data
        } catch (error) {
            console.error('Delete session error:', error)
            throw error
        }
    }

    /**
     * Check if a session is active
     * @returns {boolean} True if session exists
     */
    hasActiveSession () {
        return this.sessionId !== null
    }

    /**
     * Get the current session ID
     * @returns {string|null} Session ID
     */
    getSessionId () {
        return this.sessionId
    }

    /**
     * Check if a log is loaded
     * @returns {boolean} True if log is loaded
     */
    isLogLoaded () {
        return this.hasLog
    }
}

// Export a singleton instance
export default new ChatbotService()
