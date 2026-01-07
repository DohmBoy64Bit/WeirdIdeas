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
    // Stats
    name: document.getElementById('charName'),
    race: document.getElementById('charRace'),
    level: document.getElementById('statLevel'),
    exp: document.getElementById('statExp'),
    next: document.getElementById('statNext'),
    bar: document.getElementById('expBar'),
    hpCur: document.getElementById('statHpCur'),
    hpMax: document.getElementById('statHpMax'),
    hpBar: document.getElementById('hpBar'),

    str: document.getElementById('statStr'),
    dex: document.getElementById('statDex'),
    int: document.getElementById('statInt'),
    vit: document.getElementById('statVit'),

    pl: document.getElementById('hudPL'),
    roomName: document.getElementById('roomName'),
    roomDesc: document.getElementById('roomDesc'),
    entities: document.getElementById('entityList'),
    inventory: document.getElementById('inventoryList'),
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

    // HP
    const hp = p.stats.hp || (p.stats.vit * 10);
    const maxHp = p.stats.max_hp || (p.stats.vit * 10);
    els.hpCur.textContent = hp;
    els.hpMax.textContent = maxHp;
    const hpPct = Math.max(0, Math.min(100, (hp / maxHp) * 100));
    els.hpBar.style.width = hpPct + '%';

    // Stats
    els.str.textContent = p.stats.str;
    els.dex.textContent = p.stats.dex;
    els.int.textContent = p.stats.int;
    els.vit.textContent = p.stats.vit;

    // Fake PL calculation
    const pl = (p.stats.str + p.stats.dex + p.stats.int + p.stats.vit) * 10 * p.level;
    els.pl.textContent = pl.toLocaleString();

    // Inventory
    els.inventory.innerHTML = '';
    if (!p.inventory || p.inventory.length === 0) {
        els.inventory.innerHTML = '<li class="text-gray-600">Empty</li>';
    } else {
        p.inventory.forEach(slot => {
            const li = document.createElement('li');
            li.className = "flex justify-between items-center bg-gray-900 px-2 py-1 rounded border border-gray-800";
            // Check if slot is string or object (legacy support/API variance)
            // API sends list of dicts: {item_id, qty}
            const itemId = slot.item_id || slot;
            const qty = slot.qty || 1;

            // Format Name (Replace _ with Space and Title Case)
            const name = itemId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

            li.innerHTML = `<span class="text-gray-300 font-mono text-xs">${name}</span> <span class="text-yellow-600 text-xs">x${qty}</span>`;
            els.inventory.appendChild(li);
        });
    }
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

    // Update entities (Mobs)
    els.entities.innerHTML = '';
    if (room.mobs && room.mobs.length > 0) {
        room.mobs.forEach(mobId => {
            const li = document.createElement('li');
            li.className = "text-red-400 font-mono flex items-center space-x-2";
            // Format Name
            const name = mobId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            li.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span><span>${name}</span>`;
            els.entities.appendChild(li);
        });
    } else {
        els.entities.innerHTML = '<li class="text-gray-500 italic">No threats detected.</li>';
    }

    // Exits (Optional: Add visual exits list?)
    // room.exits is dict {dir: id}
    drawMinimap(room);

    // Update Image
    const imgEntry = document.getElementById('roomImage');
    // Simple mock logic for images
    let imgUrl = "https://placehold.co/800x400/0f172a/cbd5e1?text=Zone";
    if (room.id.includes("wasteland")) imgUrl = "https://placehold.co/800x400/3f2e18/a88b68?text=Wasteland";
    else if (room.id.includes("city")) imgUrl = "https://placehold.co/800x400/1e293b/94a3b8?text=West+City";
    else if (room.id.includes("capsule")) imgUrl = "https://placehold.co/800x400/e2e8f0/0f172a?text=Capsule+Corp";
    else if (room.id.includes("frieza")) imgUrl = "https://placehold.co/800x400/311b92/b39ddb?text=Frieza+Ship";
    else if (room.id.includes("start")) imgUrl = "https://placehold.co/800x400/22c55e/f0fdf4?text=Safe+Zone";

    imgEntry.src = imgUrl;
}

function drawMinimap(room) {
    const canvas = document.getElementById('miniMap');
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.parentElement.clientWidth;
    const h = canvas.height = canvas.parentElement.clientHeight;

    // Clear
    ctx.clearRect(0, 0, w, h);

    // Center layout
    const cx = w / 2;
    const cy = h / 2 + 10; // Offset down slightly
    const size = 8; // node size (bigger)
    const dist = 40; // length of path (longer)

    ctx.strokeStyle = '#0284c7'; // Cyan-600 (Darker)
    ctx.lineWidth = 3; // Thicker
    ctx.lineCap = 'round';

    // Draw Exits
    if (room.exits) {
        Object.keys(room.exits).forEach(dir => {
            let tx = cx, ty = cy;
            switch (dir) {
                case 'north': case 'n': ty -= dist; break;
                case 'south': case 's': ty += dist; break;
                case 'east': case 'e': tx += dist; break;
                case 'west': case 'w': tx -= dist; break;
                case 'northwest': case 'nw': tx -= dist * 0.7; ty -= dist * 0.7; break;
                case 'northeast': case 'ne': tx += dist * 0.7; ty -= dist * 0.7; break;
                case 'southwest': case 'sw': tx -= dist * 0.7; ty += dist * 0.7; break;
                case 'southeast': case 'se': tx += dist * 0.7; ty += dist * 0.7; break;
                case 'up': case 'u': tx += dist * 0.5; ty -= dist * 0.5; break;
                case 'down': case 'd': tx -= dist * 0.5; ty += dist * 0.5; break;
                case 'enter': tx = cx; ty = cy; break;
                case 'exit': tx = cx; ty = cy + dist * 1.5; break;
            }

            // Draw Line
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            // Draw Node
            ctx.fillStyle = '#0ea5e9'; // Cyan-500
            ctx.beginPath();
            ctx.arc(tx, ty, size / 2, 0, Math.PI * 2);
            ctx.fill();

            // Label
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 12px monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            let lx = tx, ly = ty;
            // Push label out further
            const labelOffset = 15;
            if (ty < cy) ly -= labelOffset;
            if (ty > cy) ly += labelOffset;
            if (tx < cx) lx -= labelOffset;
            if (tx > cx) lx += labelOffset;

            ctx.fillText(dir.substring(0, 1).toUpperCase(), lx, ly);
        });
    }

    // Draw Player
    ctx.fillStyle = '#fbbf24'; // Amber-400
    ctx.shadowColor = '#fbbf24';
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.arc(cx, cy, size, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0; // Reset
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
