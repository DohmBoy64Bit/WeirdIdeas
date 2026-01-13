import React, {useState} from 'react';

export default function Login({onLogin}){
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleLogin(){
    setLoading(true); setError(null);
    try{
      const res = await fetch('/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,password})});
      if (!res.ok){
        const err = await res.json();
        setError(err.detail || 'Login failed');
        setLoading(false); return;
      }
      const data = await res.json();
      // store token
      localStorage.setItem('pixolve_token', data.access_token);
      onLogin({username, token: data.access_token});
    }catch(e){
      setError('Network error');
    }finally{setLoading(false)}
  }

  async function handleRegister(){
    setLoading(true); setError(null);
    try{
      const res = await fetch('/auth/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,password})});
      if (!res.ok){
        const err = await res.json();
        setError(err.detail || 'Register failed');
        setLoading(false); return;
      }
      // auto-login after register
      await handleLogin();
    }catch(e){ setError('Network error') }finally{setLoading(false)}
  }

  return (
    <div className="pixel-container neon-panel" style={{maxWidth:520}}>
      <h1 className="h1">Pixolve</h1>
      <p className="small-muted">Retro pixel guessing game</p>
      <div style={{marginTop:12}}>
        <label className="px-small">Username</label>
        <div><input autoFocus value={username} onChange={e=>setUsername(e.target.value)} placeholder="Choose a username" /></div>
      </div>
      <div style={{marginTop:8}}>
        <label className="px-small">Password</label>
        <div><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Secret" /></div>
      </div>
      {error && <div style={{color:'#ff8080', marginTop:8}}>{error}</div>}
      <div style={{marginTop:12, display:'flex', gap:8}}>
        <button className="btn" onClick={handleLogin} disabled={loading}>{loading? '...' : 'Login'}</button>
        <button className="btn" onClick={handleRegister} disabled={loading}>Register</button>
      </div>
      <div style={{marginTop:12, display:'flex', justifyContent:'space-between'}}>
        <div className="small-muted">Neon pixel theme</div>
        <div className="small-muted">Token: 7 days</div>
      </div>
    </div>
  )
}