// frontend/App.jsx
import React, {useState, useEffect} from 'react';
import './styles.css';
import Login from './components/Login';
import Lobby from './components/Lobby';
import AdminPanel from './components/AdminPanel';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('pixolve_token'));
  const [view, setView] = useState('lobby'); // 'lobby' or 'admin'

  useEffect(()=>{
    if (token){
      // Fetch profile to validate token
      fetch('/auth/me', {headers: {"Authorization": `Bearer ${token}`}}).then(async res=>{
        if (res.ok){
          const p = await res.json();
          setUser(p);
        } else {
          // Token is invalid - clear it and force re-login
          console.log('Token validation failed, clearing token');
          localStorage.removeItem('pixolve_token');
          localStorage.removeItem('pixolve_username');
          setToken(null);
          setUser(null);
        }
      }).catch((err)=>{
        console.error('Error validating token:', err);
        // Network error - clear token to be safe
        localStorage.removeItem('pixolve_token');
        localStorage.removeItem('pixolve_username');
        setToken(null);
        setUser(null);
      })
    }
  },[token])

  function onLogin({username, token}){
    localStorage.setItem('pixolve_username', username);
    localStorage.setItem('pixolve_token', token);
    setToken(token);
    setUser({username});
  }

  if (!token) return (
    <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', minHeight: '100vh'}}>
      <Login onLogin={onLogin} />
    </div>
  )

  return (
    <div style={{display: 'flex', justifyContent: 'center', alignItems: 'flex-start', width: '100%', minHeight: '100vh', padding: '20px'}}>
      <div style={{width: '100%', maxWidth: '1400px'}}>
        {/* Navigation */}
        <div style={{display: 'flex', gap: '12px', marginBottom: '20px', justifyContent: 'center'}}>
          <button
            className={`btn ${view === 'lobby' ? 'btn-ready' : ''}`}
            onClick={() => setView('lobby')}
          >
            Lobby
          </button>
          <button
            className={`btn ${view === 'admin' ? 'btn-ready' : ''}`}
            onClick={() => setView('admin')}
          >
            Admin Panel
          </button>
        </div>

        {/* Content */}
        {view === 'lobby' ? (
          <Lobby user={user} token={token} />
        ) : (
          <AdminPanel user={user} token={token} />
        )}
      </div>
    </div>
  );
}

export default App;