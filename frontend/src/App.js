import { useEffect, useState } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import FingerprintJS from '@fingerprintjs/fingerprintjs';
import Home from './pages/Home';
import Calendar from './pages/Calendar';
import { Toaster } from './components/ui/sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fingerprint, setFingerprint] = useState(null);

  useEffect(() => {
    // Initialize fingerprint with session ID
    const initFingerprint = async () => {
      const fp = await FingerprintJS.load();
      const result = await fp.get();
      
      // Get or create session ID for this browser session
      let sessionId = sessionStorage.getItem('session_id');
      if (!sessionId) {
        sessionId = `${Date.now()}_${Math.random().toString(36).substring(7)}`;
        sessionStorage.setItem('session_id', sessionId);
      }
      
      // Combine device fingerprint with session ID
      const uniqueFingerprint = `${result.visitorId}_${sessionId}`;
      setFingerprint(uniqueFingerprint);
      
      // Check if user exists for this session
      try {
        const response = await fetch(`${API}/users/by-fingerprint/${uniqueFingerprint}`);
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        }
      } catch (error) {
        console.error('Error checking user:', error);
      } finally {
        setLoading(false);
      }
    };

    initFingerprint();
  }, []);

  const handleLogout = () => {
    // Clear session - this will force new registration on next visit
    sessionStorage.removeItem('session_id');
    setUser(null);
    // Reload to get new session ID
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#0a0a0a]">
        <div className="text-white text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="App dark">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={
              user ? (
                <Calendar user={user} setUser={setUser} onLogout={handleLogout} />
              ) : (
                <Home fingerprint={fingerprint} setUser={setUser} />
              )
            } 
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;