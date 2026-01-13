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
    <div className="pixel-container neon-panel" style={{maxWidth:520, margin: '0 auto', padding: '32px'}}>
      <h1 className="h1" style={{textAlign: 'center', marginBottom: '16px'}}>Pixolve</h1>
      <p className="small-muted" style={{textAlign: 'center', marginBottom: '32px'}}>Retro pixel guessing game</p>
      <div style={{marginTop:20}}>
        <label className="px-small" style={{display:'block', marginBottom:8}}>Username</label>
        <div><input autoFocus value={username} onChange={e=>setUsername(e.target.value)} placeholder="Choose a username" /></div>
      </div>
      <div style={{marginTop:16}}>
        <label className="px-small" style={{display:'block', marginBottom:8}}>Password</label>
        <div><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Secret" /></div>
      </div>
      {error && <div style={{color:'#ff8080', marginTop:12, fontSize:'10px'}}>{error}</div>}
      <div style={{marginTop:20, display:'flex', gap:12}}>
        <button className="btn btn-login" onClick={handleLogin} disabled={loading}>{loading? '...' : 'Login'}</button>
        <button className="btn btn-register" onClick={handleRegister} disabled={loading}>Register</button>
      </div>
    </div>
  )
}