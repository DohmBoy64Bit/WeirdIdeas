import React, {useEffect, useRef, useState} from 'react';

export default function Game({ws, lobbyId, token, user}){
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  const [pixelation, setPixelation] = useState(32);
  const [messages, setMessages] = useState([]);
  const [guess, setGuess] = useState('');
  const [scores, setScores] = useState({});
  const [currentImage, setCurrentImage] = useState('/placeholder.png');
  const [currentRound, setCurrentRound] = useState(0);
  const [gameFinished, setGameFinished] = useState(false);
  const [finalScores, setFinalScores] = useState({});

  useEffect(()=>{
    // listen to ws messages from parent (they will call handleMsg)
    if (!ws) return;
    const handler = (ev) => {
      try{
        const msg = JSON.parse(ev.data);
        if (msg.type === 'start_round'){
          // Load new image for the round
          setCurrentRound(msg.data.round_index);
          const imageUrl = msg.data.image_id || '/placeholder.png';
          setCurrentImage(imageUrl);
          setPixelation(32); // Reset pixelation
          setMessages(m => [...m, `Round ${msg.data.round_index + 1} started`]);
        } else if (msg.type === 'reveal_step'){
          // smooth transition: fade out overlay briefly
          const prev = pixelation;
          setPixelation(msg.data.pixelation);
          // optional: flash border on reveal
        } else if (msg.type === 'guess_result'){
          const result = msg.data;
          if (result.correct) {
            setMessages(m => [...m, `✓ ${result.player_id} got it! +${result.points_awarded}pts`]);
            // visual cue
            const canvas = canvasRef.current;
            if (canvas){ canvas.style.boxShadow = '0 0 24px rgba(0,255,247,0.18)'; setTimeout(()=>canvas.style.boxShadow='none',300); }
          } else {
            setMessages(m => [...m, `✗ ${result.player_id} guessed wrong`]);
          }
        } else if (msg.type === 'scoreboard_update'){
          setScores(msg.data.scores || {})
        } else if (msg.type === 'end_round'){
          setMessages(m => [...m, `Round ${msg.data.round_index + 1} ended`])
        } else if (msg.type === 'game_finished'){
          setGameFinished(true);
          setFinalScores(msg.data.scores || scores);
          setScores(msg.data.scores || scores);
          setMessages(m => [...m, `Game finished! Final scores:`]);
        }
      }catch(e){
        console.error('Error handling message:', e);
      }
    };
    ws.addEventListener('message', handler);
    // remove on cleanup
    return ()=>{ try{ ws.removeEventListener('message', handler); }catch(e){} };
  },[ws, scores]);

  useEffect(()=>{
    // draw image with pixelation
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;
    
    // Update image source when currentImage changes
    if (img.src !== currentImage && currentImage) {
      img.src = currentImage;
    }
    
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;

    function draw(){
      if (!img.complete || !img.naturalWidth) return;
      
      const w = canvas.width = img.naturalWidth || 800;
      const h = canvas.height = img.naturalHeight || 600;
      
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
    
    if (img.complete) {
      draw();
    } else {
      img.onload = draw;
    }
  },[pixelation, currentImage]);

  function handleSubmitGuess(){
    if (!ws) return;
    ws.send(JSON.stringify({type: 'submit_guess', data: {player_id: user.username, text: guess}}));
    setGuess('');
  }

  if (gameFinished) {
    // Game finished - show results
    const sortedScores = Object.entries(finalScores || scores)
      .sort((a, b) => b[1] - a[1])
      .map(([player, score], index) => ({ player, score, rank: index + 1 }));
    
    return (
      <div className="pixel-container" style={{maxWidth:600, margin:'40px auto'}}>
        <div className="panel neon-panel">
          <h2 className="h2">Game Finished!</h2>
          <div style={{marginTop:16}}>
            <h3 className="h2" style={{fontSize:14}}>Final Scores</h3>
            {sortedScores.length === 0 ? (
              <div className="small-muted">No scores recorded</div>
            ) : (
              <div style={{marginTop:12}}>
                {sortedScores.map(({player, score, rank}) => (
                  <div key={player} style={{
                    display:'flex',
                    justifyContent:'space-between',
                    padding:'8px 12px',
                    marginBottom:8,
                    background: rank === 1 ? 'rgba(0,255,247,0.1)' : 'rgba(255,255,255,0.02)',
                    border: rank === 1 ? '2px solid var(--accent)' : '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <span>
                      <strong>#{rank}</strong> {player}
                      {rank === 1 && <span style={{marginLeft:8, color:'var(--accent)'}}>🏆</span>}
                    </span>
                    <span><strong>{score}</strong> pts</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pixel-container grid">
      <div className="panel neon-panel">
        <h2 className="h2">Round {currentRound + 1}</h2>
        <canvas style={{width:'100%', height:240, background:'#000', imageRendering:'pixelated'}} ref={canvasRef}></canvas>
        {/* hidden image source */}
        <img ref={imgRef} src={currentImage} alt="game image" style={{display:'none'}} crossOrigin="anonymous" />
        <div style={{marginTop:8}}>
          <input 
            value={guess} 
            onChange={e=>setGuess(e.target.value)} 
            placeholder="Your guess" 
            onKeyDown={e=>{ if(e.key==='Enter') handleSubmitGuess(); }}
          />
          <button className="btn" onClick={handleSubmitGuess} style={{marginLeft:8}}>Submit</button>
        </div>
      </div>

      <div>
        <div className="panel neon-panel">
          <h2 className="h2">Messages</h2>
          <div className="chat" style={{maxHeight:200, overflow:'auto'}}>
            {messages.length===0 && <div className="small-muted">Waiting for round to start...</div>}
            {messages.map((m,i)=><div key={i} style={{marginBottom:4}}>{m}</div>)}
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
                  <span><strong>{pts}</strong></span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  )
}