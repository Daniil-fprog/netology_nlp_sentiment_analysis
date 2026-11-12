const API_BASE = "/api";

const form = document.querySelector("#upload-form");
const input = document.querySelector("#audio-input");
const button = document.querySelector("#submit-button");
const fileLabel = document.querySelector("#file-label");
const statusLine = document.querySelector("#status");
const results = document.querySelector("#results");
const count = document.querySelector("#record-count");
const template = document.querySelector("#result-template");

let sessionId = null;
let records = [];

async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (sessionId) headers.set("X-Session-ID", sessionId);
    const response = await fetch(`${API_BASE}${path}`, {...options, headers});
    if (!response.ok) {
        let message = `Ошибка ${response.status}`;
        try {
            const payload = await response.json();
            message = payload.detail || message;
        } catch (_) {
            // The server may return a non-JSON proxy error.
        }
        throw new Error(message);
    }
    return response.status === 204 ? null : response.json();
}

function setStatus(message, kind = "") {
    statusLine.textContent = message;
    statusLine.className = `status ${kind}`;
}

function render() {
    results.replaceChildren();
    count.textContent = String(records.length);
    if (!records.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "Здесь появятся тональность и расшифровка.";
        results.append(empty);
        return;
    }

    for (const record of records) {
        const node = template.content.cloneNode(true);
        const card = node.querySelector(".result-card");
        const positive = record.sentiment_label === "positive";
        node.querySelector(".result-card__file").textContent = record.original_filename;
        node.querySelector(".result-card__time").textContent = new Intl.DateTimeFormat("ru-RU", {
            dateStyle: "medium", timeStyle: "short"
        }).format(new Date(record.created_at));
        const sentiment = node.querySelector(".sentiment");
        sentiment.textContent = positive ? "Позитивная" : "Негативная";
        sentiment.classList.add(positive ? "sentiment--positive" : "sentiment--negative");
        card.classList.add(positive ? "result-card--positive" : "result-card--negative");
        node.querySelector(".confidence").textContent = `${record.model_confidence.toFixed(1)}%`;
        node.querySelector(".score").textContent = `${record.sentiment_score.toFixed(1)}/100`;
        node.querySelector(".transcript").textContent = record.transcript;
        results.append(node);
    }
}

async function startSession() {
    try {
        const session = await api("/sessions", {method: "POST"});
        sessionId = session.id;
        button.disabled = !input.files.length;
        setStatus("Сессия готова. Аудио не хранится после обработки.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

input.addEventListener("change", () => {
    const file = input.files[0];
    fileLabel.textContent = file ? file.name : "Выберите аудио";
    button.disabled = !file || !sessionId;
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = input.files[0];
    if (!file || !sessionId) return;

    const data = new FormData();
    data.append("audio", file);
    button.disabled = true;
    setStatus("Распознаём речь и анализируем тональность. Первый запуск может занять дольше…");
    try {
        const record = await api("/records", {method: "POST", body: data});
        records.unshift(record);
        render();
        form.reset();
        fileLabel.textContent = "Выберите аудио";
        setStatus("Анализ готов.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        button.disabled = !input.files.length || !sessionId;
    }
});

window.addEventListener("pagehide", (event) => {
    if (event.persisted || !sessionId) return;
    navigator.sendBeacon(`${API_BASE}/sessions/${sessionId}/close`, new Blob([], {type: "text/plain"}));
    sessionId = null;
});

startSession();
