// frontend/App.jsx
import React, {useState, useEffect} from 'react';
import './styles.css';
import Login from './components/Login';
import Lobby from './components/Lobby';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('pixolve_token'));

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

  if (!token) return <Login onLogin={onLogin} />

  return (
    <div>
      <Lobby user={user} token={token} />
    </div>
  );
}

export default App;