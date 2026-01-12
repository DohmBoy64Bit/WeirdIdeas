import React, {useEffect, useRef, useState} from 'react';

export default function Game({ws, lobbyId, token, user}){
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  const [pixelation, setPixelation] = useState(32);
  const [messages, setMessages] = useState([]);
  const [guess, setGuess] = useState('');
  const [scores, setScores] = useState({});

  useEffect(()=>{
    // listen to ws messages from parent (they will call handleMsg)
    if (!ws) return;
    const handler = (ev) => {
      try{
        const msg = JSON.parse(ev.data);
        if (msg.type === 'reveal_step'){
          // smooth transition: fade out overlay briefly
          const prev = pixelation;
          setPixelation(msg.data.pixelation);
          // optional: flash border on reveal
        } else if (msg.type === 'guess_result'){
          setMessages(m => [...m, JSON.stringify(msg.data)])
          if (msg.data.correct){
            // visual cue
            const canvas = canvasRef.current;
            if (canvas){ canvas.style.boxShadow = '0 0 24px rgba(0,255,247,0.18)'; setTimeout(()=>canvas.style.boxShadow='none',300); }
          }
        } else if (msg.type === 'scoreboard_update'){
          setScores(msg.data.scores || {})
        } else if (msg.type === 'end_round'){
          setMessages(m => [...m, `Round ${msg.data.round_index} ended`])
        }
      }catch(e){}
    };
    ws.addEventListener('message', handler);
    // remove on cleanup
    return ()=>{ try{ ws.removeEventListener('message', handler); }catch(e){} };
  },[ws]);

  useEffect(()=>{
    // draw image with pixelation
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = img.naturalWidth;
    const h = canvas.height = img.naturalHeight;
    ctx.imageSmoothingEnabled = false;

    function draw(){
      if (pixelation <= 0){
        ctx.clearRect(0,0,w,h);
        ctx.drawImage(img,0,0,w,h);
      } else {
        const sx = Math.max(1, Math.floor(w / pixelation));
        const sy = Math.max(1, Math.floor(h / pixelation));
        // draw to small offscreen canvas
        const off = document.createElement('canvas');
        off.width = sx; off.height = sy;
        const octx = off.getContext('2d');
        octx.imageSmoothingEnabled = false;
        octx.drawImage(img, 0, 0, sx, sy);
        // scale up
        ctx.clearRect(0,0,w,h);
        ctx.drawImage(off, 0, 0, sx, sy, 0, 0, w, h);
      }
    }
    draw();
  },[pixelation]);

  function handleSubmitGuess(){
    if (!ws) return;
    ws.send(JSON.stringify({type: 'submit_guess', data: {player_id: user.username, text: guess}}));
    setGuess('');
  }

  return (
    <div className="pixel-container grid">
      <div className="panel neon-panel">
        <h2 className="h2">Round</h2>
        <canvas style={{width:'100%', height:240, background:'#000', imageRendering:'pixelated'}} ref={canvasRef}></canvas>
        {/* hidden image source */}
        <img ref={imgRef} src="/placeholder.png" alt="image" style={{display:'none'}} onLoad={()=>{ /* trigger draw */ }} />
        <div style={{marginTop:8}}>
          <input value={guess} onChange={e=>setGuess(e.target.value)} placeholder="Your guess" />
          <button className="btn" onClick={handleSubmitGuess} style={{marginLeft:8}}>Submit</button>
        </div>
      </div>

      <div>
        <div className="panel neon-panel">
          <h2 className="h2">Messages</h2>
          <div className="chat">{messages.map((m,i)=><div key={i}>{m}</div>)}</div>
        </div>

        <div className="panel neon-panel" style={{marginTop:12}}>
          <h2 className="h2">Scoreboard</h2>
          <div className="scoreboard">
            {Object.keys(scores).length===0 && <div className="small-muted">No scores yet</div>}
            {Object.entries(scores).map(([p,pts])=> <div key={p}>{p}: {pts}</div>)}
          </div>
        </div>
      </div>
    </div>
  )
}