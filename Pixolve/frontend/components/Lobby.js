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

  useEffect(()=>{
    // load categories for lobby creation
    fetch('/categories').then(async res=>{
      if (res.ok){
        const data = await res.json();
        setCategories(data);
        if (data.length>0) setSelectedCategory(data[0].id);
      }
    }).catch(()=>{});
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
    if (!token) return;
    const url = `${(location.protocol==='https:'?'wss':'ws')}://${location.host}/ws?token=${encodeURIComponent(token)}&lobby=${encodeURIComponent(lobbyId)}`;
    wsRef.current = new WebSocket(url);
    wsRef.current.onopen = ()=>{
      // announce presence
      try{ wsRef.current.send(JSON.stringify({type:'join_lobby', data: {player:{id:user.username, username:user.username}}})); }catch(e){}
      console.log('ws open');
    };

    // add message listener so other components can also listen without clobbering handlers
    const msgHandler = (ev) => { try{ const msg = JSON.parse(ev.data); handleMsg(msg); }catch(e){} };
    wsRef.current.addEventListener('message', msgHandler);
    // remember handler for cleanup
    wsRef.current._msgHandler = msgHandler;

    wsRef.current.onclose = ()=>{
      console.log('ws closed');
      try{ if (wsRef.current && wsRef.current._msgHandler) wsRef.current.removeEventListener('message', wsRef.current._msgHandler); }catch(e){}
      wsRef.current = null;
    }

    wsRef.current.onerror = (e)=>{ console.warn('ws error', e); }

    window.PIXOLVE_WS = wsRef.current; // debugging hook
  }

  function startGame(){
    if (!wsRef.current) return;
    wsRef.current.send(JSON.stringify({type:'start_game', data: {player: {id:user.username, username:user.username}}}));
  }

  function handleMsg(msg){
    const t = msg.type;
    if (t === 'lobby_update'){
      setPlayers(msg.data.players || []);
      // make sure lobby reference exists
      setLobby(prev => ({...prev, players: msg.data.players}));
    } else if (t === 'chat'){
      setChatMessages(c => [...c, msg.data]);
    } else if (t === 'guess_result'){
      // show server-validated guess result briefly in chat/messages
      setChatMessages(c => [...c, {player: msg.data.player_id, text: `[guess] ${msg.data.text} — ${msg.data.correct? 'Correct' : 'No'}`, ts: new Date().toISOString()}]);
    } else if (t === 'scoreboard_update'){
      // forward via event for child components or set local state if needed
      // we'll just add a message for visibility
      setChatMessages(c => [...c, {player:'system', text: 'Scoreboard updated', ts: new Date().toISOString()}]);
    } else if (t === 'game_started'){
      setGameStarted(true);
      setGameId(msg.data.game_id);
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
              <button className="btn" onClick={()=>{
                // toggle local ready and notify server
                if (!wsRef.current) return;
                const ready = !(players.find(p=>p.id===user.username) || {}).ready;
                wsRef.current.send(JSON.stringify({type: 'player_ready', data: {player_id: user.username, ready}}));
              }}>{(players.find(p=>p.id===user.username) || {}).ready ? 'Unready' : 'Ready'}</button>
              {lobby && (lobby.host_id === user.username) && <button className="btn" style={{marginLeft:8}} onClick={startGame} disabled={players.length<2}>Start (Host)</button>}
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="panel neon-panel">
          <h2 className="h2">Chat</h2>
          <div className="chat" id="chat-window">
            {chatMessages.length===0 && <div className="small-muted">No messages yet</div>}
            {chatMessages.map((m,i)=> (
              <div key={i} className={`chat-message ${m.player===user.username? 'me' : 'other'}`}>
                <div className="meta">{m.player} • {new Date(m.ts).toLocaleTimeString()}</div>
                <div className="text">{m.text}</div>
              </div>
            ))}
          </div>
          <div style={{display:'flex', marginTop:8}}>
            <input id="chat-input" placeholder="Say something..." onKeyDown={(e)=>{ if (e.key==='Enter'){ document.getElementById('chat-send').click(); } }} />
            <button id="chat-send" className="btn" onClick={()=>{
              const val = document.getElementById('chat-input').value;
              if (!val || !wsRef.current) return;
              const payload = {player:user.username, text: val};
              wsRef.current.send(JSON.stringify({type:'chat', data: payload}));
              // optimistic echo
              setChatMessages(c=>[...c, {player:user.username, text: val, ts: new Date().toISOString()}]);
              document.getElementById('chat-input').value='';
              const win = document.getElementById('chat-window'); win.scrollTop = win.scrollHeight;
            }} style={{marginLeft:8}}>Send</button>
          </div>
        </div>

        <div className="panel neon-panel" style={{marginTop:12}}>
          <h2 className="h2">Scoreboard</h2>
          <div className="scoreboard">Scores here</div>
        </div>
      </div>
    </div>
  )
}