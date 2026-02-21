document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const chatTranscript = document.getElementById('chat-transcript');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    // --- State ---
    let history = []; // The exact list you send to backend
    let uiMessages = []; // What you render, includes metadata for assistant messages
    const MAX_VISIBLE = 8; // Max messages to show in UI
    const API_URL = '/chat'; // Backend endpoint

    // --- Core Functions ---

    /**
     * Renders the last MAX_VISIBLE messages from the uiMessages array into the chat transcript.
     */
    const renderMessages = () => {
        chatTranscript.innerHTML = ''; // Clear existing messages
        
        const visibleMessages = uiMessages.slice(-MAX_VISIBLE);

        visibleMessages.forEach(msg => {
            const messageWrapper = document.createElement('div');
            messageWrapper.classList.add('message-bubble', msg.role);

            const contentP = document.createElement('p');
            contentP.textContent = msg.content;
            messageWrapper.appendChild(contentP);

            // If assistant message, add metadata
            if (msg.role === 'assistant') {
                const metadataDiv = document.createElement('div');
                metadataDiv.classList.add('metadata');

                // Memory badge (only show if true, per spec)
                if (msg.memory_used) {
                    const memoryBadge = document.createElement('span');
                    memoryBadge.textContent = 'Memory Used';
                    memoryBadge.classList.add('memory-badge');
                    metadataDiv.appendChild(memoryBadge);
                }

                // Sources list
                if (msg.sources && msg.sources.length > 0) {
                    const sourcesHeader = document.createElement('p');
                    sourcesHeader.textContent = 'Sources:';
                    sourcesHeader.style.marginTop = '8px';
                    sourcesHeader.style.fontWeight = 'bold';
                    
                    const sourcesList = document.createElement('ul');
                    sourcesList.classList.add('sources-list');
                    msg.sources.forEach(sourceText => {
                        const sourceItem = document.createElement('li');

                        if (msg.url) {
                            const link = document.createElement('a');
                            link.href = msg.url;
                            link.textContent = sourceText;
                            link.target = '_blank';
                            link.rel = 'noopener noreferrer';
                            sourceItem.appendChild(link);
                        } else {
                            sourceItem.textContent = sourceText;
                        }
                        sourcesList.appendChild(sourceItem);
                    });
                    metadataDiv.appendChild(sourcesHeader);
                    metadataDiv.appendChild(sourcesList);
                } else if (msg.content !== 'Thinking...' && !msg.isError) {
                    // Only show "No grounded source" for real messages, not thinking or error states
                    const noSourceP = document.createElement('p');
                    noSourceP.textContent = 'No grounded source';
                    noSourceP.style.marginTop = '8px';
                    metadataDiv.appendChild(noSourceP);
                }

                if (metadataDiv.hasChildNodes()) {
                    messageWrapper.appendChild(metadataDiv);
                }
            }

            chatTranscript.appendChild(messageWrapper);
        });

        // Scroll to the bottom to show the latest messages
        chatTranscript.scrollTop = chatTranscript.scrollHeight;
    };

    /**
     * Handles the entire message sending pipeline.
     * @param {string} messageText The user's message.
     */
    const handleSendMessage = async (messageText) => {
        // 1. Push user message to UI
        uiMessages.push({ role: 'user', content: messageText });

        // 2. Push temporary "Thinking..." message
        const thinkingMessage = { role: 'assistant', content: 'Thinking...' };
        uiMessages.push(thinkingMessage);
        renderMessages();

        // 3. Disable form
        messageInput.disabled = true;
        sendButton.disabled = true;

        try {
            // 4. Call backend
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: messageText,
                    history: history,
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! Status: ${response.status}, Body: ${errorText}`);
            }

            const data = await response.json();

            // 5. On success: Replace "Thinking..." with the real response
            uiMessages.pop(); // Remove "Thinking..."
            uiMessages.push({
                role: 'assistant',
                content: data.answer,
                memory_used: data.memory_used,
                sources: data.sources,
                url: data.url,
            });

            // 6. Update backend history
            history = data.history;

        } catch (error) {
            console.error('Error fetching chat response:', error);
            // 7. On failure: Replace "Thinking..." with an error message
            uiMessages.pop(); // Remove "Thinking..."
            uiMessages.push({
                role: 'assistant',
                content: `Sorry, something went wrong. Please try again.`,
                memory_used: false,
                sources: [],
                isError: true, // Custom flag
            });
        } finally {
            // 8. Re-enable form and re-render
            messageInput.disabled = false;
            sendButton.disabled = false;
            renderMessages();
            messageInput.focus();
        }
    };

    // --- Event Listeners ---

    messageForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const messageText = messageInput.value.trim();
        if (messageText) {
            handleSendMessage(messageText);
            messageInput.value = '';
        }
    });
});