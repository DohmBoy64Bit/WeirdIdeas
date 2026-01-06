const API_URL = "/api/v1";
const WS_URL = "ws://localhost:8000/ws";

let token = localStorage.getItem('mud_token');
if (!token) window.location.href = '/';

let socket = null;
let reconnectTimer = null;

// --- UI Elements ---
const els = {
    log: document.getElementById('gameLog'),
    input: document.getElementById('cmdInput'),
    form: document.getElementById('commandForm'),
    status: document.getElementById('connectionStatus'),
    // Stats
    name: document.getElementById('charName'),
    race: document.getElementById('charRace'),
    level: document.getElementById('statLevel'),
    exp: document.getElementById('statExp'),
    next: document.getElementById('statNext'),
    bar: document.getElementById('expBar'),
    str: document.getElementById('statStr'),
    dex: document.getElementById('statDex'),
    int: document.getElementById('statInt'),
    vit: document.getElementById('statVit'),
    pl: document.getElementById('hudPL'),
    roomName: document.getElementById('roomName'),
    roomDesc: document.getElementById('roomDesc'),
    entities: document.getElementById('entityList'),
};

// --- Initialization ---

async function init() {
    // 1. Fetch initial player state
    try {
        const res = await fetch(`${API_URL}/players/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 404) window.location.href = '/create-character';
        if (!res.ok) throw new Error("Auth failed");

        const player = await res.json();
        updateStats(player);

        // 2. Connect WS
        connectWS(player.id);

    } catch (e) {
        console.error(e);
        window.location.href = '/';
    }
}

function updateStats(p) {
    els.name.textContent = p.name;
    els.race.textContent = p.race;
    els.level.textContent = p.level;
    els.exp.textContent = p.exp;
    // Calculate next level exp (simple formula for now)
    const next = p.level * 1000;
    els.next.textContent = next;
    els.bar.style.width = Math.min(100, (p.exp / next) * 100) + '%';

    // Stats
    els.str.textContent = p.stats.str;
    els.dex.textContent = p.stats.dex;
    els.int.textContent = p.stats.int;
    els.vit.textContent = p.stats.vit;

    // Fake PL calculation
    const pl = (p.stats.str + p.stats.dex + p.stats.int + p.stats.vit) * 10 * p.level;
    els.pl.textContent = pl.toLocaleString();
}

// --- WebSocket ---

function connectWS(playerId) {
    socket = new WebSocket(`${WS_URL}/${playerId}?token=${token}`);

    socket.onopen = () => {
        els.status.textContent = "Connected";
        els.status.className = "text-xs text-green-500 uppercase";
        writeLog("System", "Neural Link Established.");
    };

    socket.onclose = () => {
        els.status.textContent = "Disconnected";
        els.status.className = "text-xs text-red-500 uppercase";
        writeLog("System", "Connection Lost. Retrying...", "channel-system");
        setTimeout(() => connectWS(playerId), 3000);
    };

    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleMessage(msg);
        } catch (e) {
            // Text fallback
            writeLog("Unknown", event.data);
        }
    };
}

function handleMessage(msg) {
    // msg structure: { type: 'chat'|'update'|'error', content: ... }

    switch (msg.type) {
        case 'chat':
            writeLog(msg.sender, msg.content, msg.channel || 'channel-say');
            break;
        case 'gamestate':
            // Full update
            if (msg.player) updateStats(msg.player);
            if (msg.room) updateRoom(msg.room);
            break;
        default:
            console.log("Unknown msg:", msg);
    }
}

function updateRoom(room) {
    els.roomName.textContent = room.name;
    els.roomDesc.textContent = room.description;
    // Update entities if present
}

function writeLog(sender, text, className = "channel-world") {
    const d = document.createElement('div');
    d.className = `chat-msg ${className}`;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    d.innerHTML = `<span class="opacity-50">[${time}]</span> <span class="font-bold">${sender}:</span> ${text}`;

    els.log.appendChild(d);
    els.log.scrollTop = els.log.scrollHeight;
}

// --- Input ---

els.form.addEventListener('submit', (e) => {
    e.preventDefault();
    const txt = els.input.value.trim();
    if (!txt) return;

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(txt);
        // Echo locally? Maybe not, wait for server ack usually
    } else {
        writeLog("System", "Not connected.", "channel-system");
    }

    els.input.value = '';
});

document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('mud_token');
    window.location.href = '/';
});

// Start
init();
