// API base URL - use relative path to work from any host
const API_URL = '/api';

// Global state
let currentSessionId = null;
let chatHistory = [];
let currentChatIndex = -1;
let activeChatIndex = -1;  // Tracks which chat the user last clicked/is viewing
let nextChatId = 1;
const MAX_CHATS = 3;

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseTitles, newChatButton, chatHistoryContainer;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements after page loads
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    newChatButton = document.getElementById('newChatButton');
    chatHistoryContainer = document.getElementById('chatHistory');
    
    setupEventListeners();
    loadChatHistory();
    createNewSession();
    loadCourseStats();
});

// Event Listeners
function setupEventListeners() {
    // Chat functionality
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // New chat button
    newChatButton.addEventListener('click', startNewChat);
    
    // Suggested questions
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


// Chat Functions
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    // Disable input
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Add user message
    addMessage(query, 'user');

    // Add loading message - create a unique container for it
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId
            })
        });

        if (!response.ok) throw new Error('Query failed');

        const data = await response.json();
        
        // Update session ID if new
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        // Replace loading message with response
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);
        
        // Save the current chat after receiving response
        saveCurrentChat();

    } catch (error) {
        // Replace loading message with error
        loadingMessage.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
        
        // Save the current chat even on error
        saveCurrentChat();
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;
    
    // Convert markdown to HTML for assistant messages
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);
    
    let html = `<div class="message-content">${displayContent}</div>`;
    
    if (sources && sources.length > 0) {
        // Remove duplicates and handle both old format (strings) and new format (objects with text/link)
        const uniqueSources = new Map();
        
        sources.forEach(source => {
            let key, displayText, link;
            
            if (typeof source === 'string') {
                key = source;
                displayText = source;
                link = null;
            } else if (source.text) {
                key = source.text;
                displayText = source.text;
                link = source.link;
            } else {
                key = String(source);
                displayText = String(source);
                link = null;
            }
            
            // Store unique sources (use first occurrence)
            if (!uniqueSources.has(key)) {
                uniqueSources.set(key, { text: displayText, link: link });
            }
        });
        
        const sourcesHtml = Array.from(uniqueSources.values()).map(source => {
            if (source.link) {
                return `<a href="${escapeHtml(source.link)}" target="_blank" rel="noopener noreferrer" class="source-badge">${escapeHtml(source.text)}</a>`;
            } else {
                return `<span class="source-badge source-badge-no-link">${escapeHtml(source.text)}</span>`;
            }
        }).join('');
        
        html += `
            <details class="sources-collapsible">
                <summary class="sources-header">Sources</summary>
                <div class="sources-content">${sourcesHtml}</div>
            </details>
        `;
    }
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

// Helper function to escape HTML for user messages
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Removed removeMessage function - no longer needed since we handle loading differently

// Chat History Functions
function loadChatHistory() {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        chatHistory = JSON.parse(saved);
    }
    const savedNextId = localStorage.getItem('nextChatId');
    if (savedNextId) {
        nextChatId = parseInt(savedNextId);
    }
    updateChatHistoryUI();
}

function saveChatHistory() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    localStorage.setItem('nextChatId', nextChatId.toString());
}

function saveCurrentChat() {
    if (currentChatIndex >= 0 && chatHistory[currentChatIndex]) {
        chatHistory[currentChatIndex].messages = Array.from(chatMessages.children).map(msg => ({
            content: msg.querySelector('.message-content').innerHTML,
            type: msg.classList.contains('user') ? 'user' : 'assistant',
            isWelcome: msg.classList.contains('welcome-message')
        }));
        chatHistory[currentChatIndex].sessionId = currentSessionId;
        saveChatHistory();
    }
}

function createNewChatEntry() {
    const chatTitle = `Chat ${nextChatId}`;
    const newChat = {
        id: Date.now(),
        title: chatTitle,
        messages: [],
        sessionId: null,
        createdAt: new Date().toISOString()
    };
    
    // If we have 3 chats, remove the oldest
    if (chatHistory.length >= MAX_CHATS) {
        chatHistory.shift();
        // Update indices for remaining chats
        if (currentChatIndex > 0) currentChatIndex--;
        else currentChatIndex = -1;
    }
    
    chatHistory.push(newChat);
    currentChatIndex = chatHistory.length - 1;
    nextChatId++;
    saveChatHistory();
    updateChatHistoryUI();
    
    return newChat;
}

function switchToChat(index) {
    // Save current chat first
    saveCurrentChat();
    
    // Switch to selected chat
    currentChatIndex = index;
    activeChatIndex = index;  // Update which chat should be highlighted
    const chat = chatHistory[index];
    currentSessionId = chat.sessionId;
    
    // Clear current messages
    chatMessages.innerHTML = '';
    
    // Restore messages
    if (chat.messages.length === 0) {
        addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
    } else {
        chat.messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.type}${msg.isWelcome ? ' welcome-message' : ''}`;
            messageDiv.innerHTML = `<div class="message-content">${msg.content}</div>`;
            chatMessages.appendChild(messageDiv);
        });
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    updateChatHistoryUI();  // Refresh UI to show new active state
}

function updateChatHistoryUI() {
    if (!chatHistoryContainer) return;
    
    if (chatHistory.length === 0) {
        chatHistoryContainer.innerHTML = '<span class="no-chats">No previous chats</span>';
        return;
    }
    
    chatHistoryContainer.innerHTML = chatHistory.map((chat, index) => `
        <button class="chat-history-item ${index === activeChatIndex ? 'active' : ''}" onclick="switchToChat(${index})">
            ${chat.title}
        </button>
    `).join('');
}

async function createNewSession() {
    currentSessionId = null;
    chatMessages.innerHTML = '';
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
}

function startNewChat() {
    // Save current chat if exists
    saveCurrentChat();
    
    // Create new chat entry
    createNewChatEntry();
    
    // Set the new chat as both current and active
    activeChatIndex = currentChatIndex;
    
    // Create a new session and clear the chat
    createNewSession();
    
    // Clear any pending input
    chatInput.value = '';
    
    // Focus on the input for immediate use
    chatInput.focus();
}

// Load course statistics
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(`${API_URL}/courses`);
        if (!response.ok) throw new Error('Failed to load course stats');
        
        const data = await response.json();
        console.log('Course data received:', data);
        
        // Update stats in UI
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        // Update course titles
        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                courseTitles.innerHTML = data.course_titles
                    .map(title => `<div class="course-title-item">${title}</div>`)
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        // Set default values on error
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}