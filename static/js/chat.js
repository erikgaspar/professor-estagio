// static/js/chat.js

// logo acima de tudo,
// garanta que existam no seu HTML dois <audio> com esses IDs:
//   <audio id="typing-sound" …>
//   <audio id="message-arrived-sound" …>

const typingSound = document.getElementById("typing-sound");
const messageArrivedSound = document.getElementById("message-arrived-sound");

// … resto do seu código …

// guarda todo o histórico de mensagens
const chatHistory = [];

// --- Lógica do Chat ---
const chatWindow = document.getElementById("chat-window");
const sendBtn = document.getElementById("send-btn");
const messageInput = document.getElementById("input-msg");
const messageTemplate = document.getElementById("message-template");

const markdownToHtml = (text) => {
    const lines = text.split('\n');
    let html = '', inList = false;
    for (const line of lines) {
        if (line.startsWith('* ')) {
            if (!inList) {
                html += '<ul class="list-disc list-inside space-y-1 my-2">';
                inList = true;
            }
            html += `<li>${line.substring(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</li>`;
        } else {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            if (line.trim() !== '') {
                html += `<p class="mb-2">${line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>`;
            }
        }
    }
    if (inList) html += '</ul>';
    return html;
};

const addMessageToChat = (sender, message, isHtml = false) => {
    const clone = messageTemplate.content.cloneNode(true);
    const div = clone.querySelector(".chat-message");
    const bubble = clone.querySelector(".message-bubble");
    div.classList.add(sender);
    bubble[isHtml ? "innerHTML" : "textContent"] = message;
    chatWindow.appendChild(clone);
    chatWindow.scrollTop = chatWindow.scrollHeight;
};

const handleSendMessage = async () => {
    const userMsg = messageInput.value.trim();
    if (!userMsg) return;

    // bloqueia UI
    sendBtn.disabled = true;
    messageInput.disabled = true;

    // adiciona ao histórico, exibe e toca o som
    chatHistory.push({ role: "user", content: userMsg });
    addMessageToChat("user", userMsg);
    typingSound.play().catch(e => console.error("Erro ao tocar som de digitação:", e));
    messageInput.value = "";
    messageInput.style.height = "auto";

    // indicador de digitando
    addMessageToChat("bot", '<div class="typing-indicator"><span></span><span></span><span></span></div>', true);
    const typingIndicator = chatWindow.querySelector('.chat-message:last-child');

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ history: chatHistory })
        });

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();
        const botReply = data.reply || "Desculpe, não consegui processar sua pergunta.";

        // remove indicador, toca som e exibe resposta
        if (typingIndicator) typingIndicator.remove();
        messageArrivedSound.play().catch(e => console.error("Erro ao tocar som de chegada:", e));

        const formatted = markdownToHtml(botReply);
        addMessageToChat("bot", formatted, true);

        // adiciona resposta ao histórico
        chatHistory.push({ role: "assistant", content: botReply });

    } catch (err) {
        if (typingIndicator) typingIndicator.remove();
        console.error("Erro:", err);
        addMessageToChat("bot", `<p>Ocorreu um erro ao buscar a resposta. Por favor, tente novamente. Detalhe: ${err.message}</p>`, true);
    } finally {
        sendBtn.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
};

sendBtn.addEventListener("click", handleSendMessage);
messageInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});
messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
});

