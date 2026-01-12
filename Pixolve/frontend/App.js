// frontend/App.js
import React, {useState, useEffect} from 'react';
import './styles.css';
import Login from './components/Login';
import Lobby from './components/Lobby';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('pixolve_token'));

  useEffect(()=>{
    if (token){
      // Fetch profile
      fetch('/auth/me', {headers: {"Authorization": `Bearer ${token}`}}).then(async res=>{
        if (res.ok){
          const p = await res.json();
          setUser(p);
        } else {
          // fallback
          const uname = localStorage.getItem('pixolve_username') || 'player';
          setUser({username: uname});
        }
      }).catch(()=>{
        const uname = localStorage.getItem('pixolve_username') || 'player';
        setUser({username: uname});
      })
    }
  },[token])

  function onLogin({username, token}){
    localStorage.setItem('pixolve_username', username);
    localStorage.setItem('pixolve_token', token);
    setToken(token);
    setUser({username});
  }

  if (!token) return <Login onLogin={onLogin} />

  return (
    <div>
      <Lobby user={user} token={token} />
    </div>
  );
}

export default App;