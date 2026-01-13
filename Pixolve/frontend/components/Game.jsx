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
  const [timeRemaining, setTimeRemaining] = useState(20);
  const [roundStarted, setRoundStarted] = useState(false);

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
          // Use image processor endpoint for pixelated image
          // Extract image path from URL (e.g., /data/images/abc123_photo.jpg -> images/abc123_photo.jpg)
          let processedUrl = imageUrl;
          if (imageUrl.startsWith('/data/')) {
            const imagePath = imageUrl.replace('/data/', '');
            processedUrl = `/categories/images/pixelated?image_path=${encodeURIComponent(imagePath)}&pixel_size=32&num_colors=16`;
          }
          setCurrentImage(processedUrl);
          setPixelation(32); // Reset pixelation
          setTimeRemaining(20); // Reset timer
          setRoundStarted(true);
          setMessages(m => [...m, `Round ${msg.data.round_index + 1} started`]);
        } else if (msg.type === 'reveal_step'){
          // Update pixelation level - use image processor endpoint
          const pixelSize = msg.data.pixelation;
          setPixelation(pixelSize);
          // Update image URL with new pixel_size
          const imageUrl = currentImage;
          if (imageUrl && imageUrl.includes('/pixelated')) {
            // Extract image_path from current URL and update pixel_size
            const url = new URL(imageUrl, window.location.origin);
            const imagePath = url.searchParams.get('image_path');
            if (imagePath) {
              const newUrl = `/categories/images/pixelated?image_path=${encodeURIComponent(imagePath)}&pixel_size=${pixelSize}&num_colors=16&t=${Date.now()}`;
              setCurrentImage(newUrl);
            }
          }
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
          setRoundStarted(false);
          setTimeRemaining(0);
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

  // Timer countdown
  useEffect(() => {
    if (!roundStarted || timeRemaining <= 0) return;
    
    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          setRoundStarted(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [roundStarted, timeRemaining]);

  useEffect(()=>{
    // Using image processor for pixelation - just display the processed image
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
      
      // Image processor handles pixelation server-side, just draw the image
      ctx.clearRect(0,0,w,h);
      ctx.drawImage(img,0,0,w,h);
    }
    
    if (img.complete) {
      draw();
    } else {
      img.onload = draw;
    }
    
    /* OLD CLIENT-SIDE PIXELATION CODE (commented out - using image processor now)
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
    */
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
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px'}}>
          <h2 className="h2">Round {currentRound + 1}</h2>
          {roundStarted && (
            <div className="px-small" style={{
              padding: '8px 12px',
              background: timeRemaining <= 5 ? 'rgba(255,68,68,0.3)' : 'rgba(0,255,247,0.2)',
              border: '2px solid',
              borderColor: timeRemaining <= 5 ? 'var(--retro-red)' : 'var(--accent)',
              fontFamily: "'Press Start 2P', monospace",
              fontSize: '12px'
            }}>
              {timeRemaining}s
            </div>
          )}
        </div>
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