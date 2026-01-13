import React, {useEffect, useState, useRef} from 'react';
import Game from './Game';

export default function Lobby({user, token}){
  const [lobby, setLobby] = useState(null);
  const [players, setPlayers] = useState([]);
  const [joinCode, setJoinCode] = useState('');
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [rounds, setRounds] = useState(5);
  const [maxPlayers, setMaxPlayers] = useState(5);
  const [chatMessages, setChatMessages] = useState([]);
  const wsRef = useRef(null);
  const [gameStarted, setGameStarted] = useState(false);
  const [gameId, setGameId] = useState(null);
  const [scores, setScores] = useState({});
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(()=>{
    // load categories for lobby creation
    fetch('/categories/').then(async res=>{
      if (res.ok){
        const data = await res.json();
        setCategories(data);
        if (data.length>0) setSelectedCategory(data[0].id);
      } else {
        console.error('Failed to load categories:', res.status, res.statusText);
      }
    }).catch((err)=>{
      console.error('Error loading categories:', err);
    });
  },[]);

  async function createLobby(){
    const payload = { max_players: maxPlayers, rounds: rounds, host_id: user.username, category: selectedCategory };
    const res = await fetch('/lobbies', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json();
    setLobby(data);
    setJoinCode(data.join_code);
    // set current players from response if present
    if (data.players) setPlayers(data.players);
    connectWs(data.id);
  }

  async function joinByCode(){
    const code = prompt('Enter join code');
    if(!code) return;
    const payload = {join_code: code, player:{id:user.username, username:user.username, display_name: user.username}};
    const res = await fetch('/lobbies/join_by_code', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    if (!res.ok){ alert('Failed to join'); return; }
    const data = await res.json();
    setLobby(data.lobby);
    setPlayers(data.players || []);
    setJoinCode(data.lobby.join_code || '');
    connectWs(data.lobby.id);
  }

  function copyCode(){
    navigator.clipboard.writeText(joinCode).then(()=>{
      // small non-blocking visual feedback
      const el = document.createElement('div');
      el.innerText = 'Copied!';
      el.style.position = 'fixed'; el.style.right = '20px'; el.style.top = '20px'; el.style.padding = '8px 12px'; el.style.background = 'linear-gradient(90deg,var(--accent),var(--accent-2))'; el.style.color = '#001'; el.style.borderRadius = '4px'; el.style.zIndex = 9999;
      document.body.appendChild(el);
      setTimeout(()=>document.body.removeChild(el), 1200);
    }).catch(()=>alert('Failed to copy'))
  }

  function connectWs(lobbyId){
    if (!token) {
      console.error('WebSocket: No token available');
      alert('No authentication token. Please log in again.');
      // Clear any stale data
      localStorage.removeItem('pixolve_token');
      localStorage.removeItem('pixolve_username');
      window.location.reload();
      return;
    }
    // Connect directly to backend (WebSocket proxy can be unreliable)
    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = 'localhost:8000';
    const url = `${wsProtocol}//${backendHost}/ws?token=${encodeURIComponent(token)}&lobby=${encodeURIComponent(lobbyId)}`;
    console.log('WebSocket: Connecting to', url);
    wsRef.current = new WebSocket(url);
    wsRef.current.onopen = ()=>{
      console.log('WebSocket: Connected successfully');
      setWsConnected(true);
      // announce presence
      try{ 
        wsRef.current.send(JSON.stringify({type:'join_lobby', data: {player:{id:user.username, username:user.username}}}));
        console.log('WebSocket: Sent join_lobby message');
      }catch(e){
        console.error('WebSocket: Error sending join_lobby', e);
      }
    };

    // add message listener so other components can also listen without clobbering handlers
    const msgHandler = (ev) => { 
      try{ 
        const msg = JSON.parse(ev.data); 
        console.log('WebSocket: Received message', msg.type);
        handleMsg(msg); 
      }catch(e){
        console.error('WebSocket: Error parsing message', e, ev.data);
      } 
    };
    wsRef.current.addEventListener('message', msgHandler);
    // remember handler for cleanup
    wsRef.current._msgHandler = msgHandler;

    wsRef.current.onclose = (event)=>{
      console.log('WebSocket: Closed', event.code, event.reason);
      setWsConnected(false);
      try{ if (wsRef.current && wsRef.current._msgHandler) wsRef.current.removeEventListener('message', wsRef.current._msgHandler); }catch(e){} 
      wsRef.current = null;
      
      // If closed due to authentication error (1008), clear token and reload
      if (event.code === 1008) {
        console.error('WebSocket: Authentication failed, clearing token');
        localStorage.removeItem('pixolve_token');
        localStorage.removeItem('pixolve_username');
        alert('Authentication failed. Please log in again.');
        window.location.reload();
      }
    }

    wsRef.current.onerror = (e)=>{ 
      console.error('WebSocket: Error', e);
      // Don't show alert on every error, just log it
      // The onclose handler will handle auth errors
    }

    window.PIXOLVE_WS = wsRef.current; // debugging hook
  }

  function startGame(){
    if (!wsRef.current || !wsConnected) {
      console.error('Start game: WebSocket not connected');
      alert('Not connected to lobby. Please wait for connection.');
      return;
    }
    if (wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('Start game: WebSocket not open, state:', wsRef.current.readyState);
      alert('Connection lost. Please refresh.');
      return;
    }
    try {
      console.log('Sending start_game message');
      wsRef.current.send(JSON.stringify({type:'start_game', data: {player: {id:user.username, username:user.username}}}));
    } catch(err) {
      console.error('Error sending start_game:', err);
      alert('Failed to start game: ' + err.message);
    }
  }

  function handleMsg(msg){
    const t = msg.type;
    console.log('Handling message type:', t, msg.data);
    if (t === 'lobby_update'){
      const updatedPlayers = msg.data.players || [];
      console.log('Updating players:', updatedPlayers);
      setPlayers(updatedPlayers);
      // make sure lobby reference exists
      setLobby(prev => prev ? {...prev, players: updatedPlayers} : prev);
    } else if (t === 'chat'){
      setChatMessages(c => [...c, msg.data]);
    } else if (t === 'guess_result'){
      // show server-validated guess result briefly in chat/messages
      setChatMessages(c => [...c, {player: msg.data.player_id, text: `[guess] ${msg.data.text} — ${msg.data.correct? 'Correct' : 'No'}`, ts: new Date().toISOString()}]);
    } else if (t === 'scoreboard_update'){
      // Update scoreboard state
      setScores(msg.data.scores || {});
    } else if (t === 'game_started'){
      console.log('Game started!', msg.data);
      setGameStarted(true);
      setGameId(msg.data.game_id);
    } else if (t === 'error'){
      console.error('Server error:', msg.data);
      alert('Error: ' + msg.data);
    } else if (t === 'unknown_event'){
      console.log('unknown_event', msg.data);
    }
  }

  // auto-scroll chat when messages change
  useEffect(()=>{
    const win = document.getElementById('chat-window');
    if (win) win.scrollTop = win.scrollHeight;
  },[chatMessages]);

  useEffect(()=>{
    return ()=>{
      if (wsRef.current){
        try{ wsRef.current.close(); }catch(e){}
      }
    }
  },[])

  if (gameStarted && wsRef.current && lobby){
    return <Game ws={wsRef.current} lobbyId={lobby.id} token={token} user={user} />
  }

  return (
    <div className="pixel-container grid">
      <div className="panel neon-panel">
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
          <h2 className="h2">Lobby</h2>
          {user && (
            <div style={{textAlign:'right'}}>
              <div className="px-small">{user.display_name || user.username}</div>
              <div className="small-muted">Level {user.level || 1} • XP {user.xp || 0}</div>
            </div>
          )}
        </div>
        {!lobby && (
          <div>
            <div style={{marginTop:8}}>
              <label className="px-small">Category</label>
              <div>
                <select value={selectedCategory || ''} onChange={e=>setSelectedCategory(e.target.value)}>
                  {categories.map(c=> <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              {selectedCategory && <div className="small-muted" style={{marginTop:6}}>{(categories.find(c=>c.id===selectedCategory)||{}).description}</div>}
            </div>

            <div style={{marginTop:8}}>
              <label className="px-small">Rounds</label>
              <div><input type="number" value={rounds} onChange={e=>setRounds(Number(e.target.value))} min={1} max={20} /></div>
            </div>

            <div style={{marginTop:8}}>
              <label className="px-small">Max players</label>
              <div><input type="number" value={maxPlayers} onChange={e=>setMaxPlayers(Number(e.target.value))} min={2} max={20} /></div>
            </div>

            <div style={{marginTop:12}}>
              <button className="btn" onClick={createLobby}>Create Lobby</button>
              <button className="btn" onClick={joinByCode} style={{marginLeft:8}}>Join by Code</button>
            </div>
          </div>
        )}

        {lobby && (
          <div style={{marginTop:12}}>
            <div><span className="small-muted">Join code</span></div>
            <div style={{marginTop:6}}>
              <span className="join-code">{joinCode}</span>
              <button className="copy-btn" onClick={copyCode}>Copy</button>
            </div>

            <div style={{marginTop:12}}>
              <div className="small-muted">Category</div>
              <div style={{marginTop:6}}>{(categories.find(c=>c.id===lobby.category)||{}).name || lobby.category || '—'}</div>
            </div>

            <div style={{marginTop:12}}>
              <div className="small-muted">Players</div>
              <ul>
                {players.map(p=> <li key={p.id} className="player-row" style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}><span>{p.username}{p.id===lobby.host_id && <strong style={{marginLeft:8}} className="badge">Host</strong>}</span><span className="small-muted">{p.ready? 'Ready' : ''}</span></li>)}
              </ul>
            </div>
            <div style={{marginTop:12}}>
              <button 
                className="btn" 
                disabled={!wsConnected}
                onClick={(e)=>{
                  e.preventDefault();
                  if (!wsRef.current || !wsConnected) {
                    console.error('Ready: WebSocket not connected');
                    alert('Not connected. Please wait for connection.');
                    return;
                  }
                  try {
                    // toggle local ready and notify server
                    const currentPlayer = players.find(p=>p.id===user.username) || {};
                    const ready = !currentPlayer.ready;
                    console.log('Sending player_ready:', {player_id: user.username, ready});
                    wsRef.current.send(JSON.stringify({type: 'player_ready', data: {player_id: user.username, ready}}));
                  } catch(err) {
                    console.error('Error sending ready state:', err);
                    alert('Failed to update ready state: ' + err.message);
                  }
                }}
              >
                {(players.find(p=>p.id===user.username) || {}).ready ? 'Unready' : 'Ready'}
              </button>
              {lobby && (lobby.host_id === user.username) && (
                <button 
                  className="btn" 
                  style={{marginLeft:8}} 
                  onClick={(e)=>{
                    e.preventDefault();
                    if (!wsConnected || !wsRef.current) {
                      console.error('Start: WebSocket not connected');
                      alert('Not connected. Please wait for connection.');
                      return;
                    }
                    if (players.length < 2) {
                      alert('Need at least 2 players to start');
                      return;
                    }
                    try {
                      console.log('Sending start_game');
                      startGame();
                    } catch(err) {
                      console.error('Error starting game:', err);
                      alert('Failed to start game: ' + err.message);
                    }
                  }} 
                  disabled={!wsConnected || players.length<2}
                >
                  Start (Host)
                </button>
              )}
              <button 
                className="btn" 
                style={{marginLeft:8}} 
                onClick={async (e)=>{
                  e.preventDefault();
                  if (!lobby) {
                    console.error('Leave: No lobby');
                    return;
                  }
                  try {
                    console.log('Leaving lobby:', lobby.id, 'User:', user);
                    const playerData = {
                      id: user.username || user.id,
                      username: user.username,
                      display_name: user.display_name || user.username,
                      ready: false
                    };
                    console.log('Sending leave request with data:', playerData);
                    const res = await fetch(`/lobbies/${lobby.id}/leave`, {
                      method:'POST',
                      headers:{'Content-Type':'application/json'},
                      body:JSON.stringify(playerData)
                    });
                    console.log('Leave response status:', res.status, res.statusText);
                    if (res.ok) {
                      console.log('Left lobby successfully');
                      if (wsRef.current) {
                        wsRef.current.close();
                      }
                      setLobby(null);
                      setPlayers([]);
                      setJoinCode('');
                      setGameStarted(false);
                      setWsConnected(false);
                      setScores({});
                      setChatMessages([]);
                    } else {
                      let errorMsg = 'Unknown error';
                      try {
                        const errorData = await res.json();
                        console.error('Leave error response:', errorData);
                        errorMsg = errorData.detail || errorData.message || String(errorData);
                      } catch(parseErr) {
                        console.error('Failed to parse error response:', parseErr);
                        errorMsg = `HTTP ${res.status}: ${res.statusText}`;
                      }
                      console.error('Failed to leave lobby:', errorMsg);
                      alert('Failed to leave lobby: ' + errorMsg);
                    }
                  } catch(e) {
                    console.error('Error leaving lobby:', e);
                    const errorMsg = e.message || e.toString() || 'Network error';
                    alert('Failed to leave lobby: ' + errorMsg);
                  }
                }}
              >
                Leave
              </button>
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="panel neon-panel">
          <h2 className="h2">Chat</h2>
          <div className="chat" id="chat-window">
            {chatMessages.length===0 && (
              <div className="small-muted">
                {!lobby || !wsConnected 
                  ? 'Join a lobby to start chatting' 
                  : 'No messages yet'}
              </div>
            )}
            {chatMessages.map((m,i)=> (
              <div key={i} className={`chat-message ${m.player===user.username? 'me' : 'other'}`}>
                <div className="meta">{m.player} • {new Date(m.ts).toLocaleTimeString()}</div>
                <div className="text">{m.text}</div>
              </div>
            ))}
          </div>
          <div style={{display:'flex', marginTop:8}}>
            <input 
              id="chat-input" 
              placeholder={!lobby || !wsConnected ? "Join a lobby to chat..." : "Say something..."} 
              disabled={!lobby || !wsConnected}
              onKeyDown={(e)=>{ 
                if (e.key==='Enter' && !e.target.disabled){ 
                  e.preventDefault();
                  const btn = document.getElementById('chat-send');
                  if (btn && !btn.disabled) btn.click();
                } 
              }} 
            />
            <button 
              id="chat-send" 
              className="btn" 
              disabled={!lobby || !wsConnected}
              onClick={(e)=>{
                e.preventDefault();
                if (!lobby || !wsRef.current || !wsConnected) {
                  console.error('Chat: WebSocket not connected');
                  return;
                }
                try {
                  const input = document.getElementById('chat-input');
                  const val = input ? input.value : '';
                  if (!val || !val.trim()) {
                    console.log('Chat: empty message, ignoring');
                    return;
                  }
                  const payload = {player:user.username, text: val.trim()};
                  console.log('Chat: sending message', payload);
                  wsRef.current.send(JSON.stringify({type:'chat', data: payload}));
                  // Clear input - message will appear when server broadcasts it back
                  if (input) input.value='';
                } catch (err) {
                  console.error('Chat: error sending message', err);
                  alert('Failed to send message: ' + err.message);
                }
              }} 
              style={{marginLeft:8}}
            >
              Send
            </button>
          </div>
        </div>

        <div className="panel neon-panel" style={{marginTop:12}}>
          <h2 className="h2">Scoreboard</h2>
          <div className="scoreboard">
            {Object.keys(scores).length===0 && <div className="small-muted">No scores yet</div>}
            {Object.entries(scores)
              .sort((a,b)=>b[1]-a[1])
              .map(([p,pts])=> (
                <div key={p} style={{
                  display:'flex',
                  justifyContent:'space-between',
                  padding:'4px 0',
                  borderBottom:'1px dashed rgba(255,255,255,0.1)'
                }}>
                  <span>{p}</span>
                  <span><strong>{pts}</strong> pts</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  )
}