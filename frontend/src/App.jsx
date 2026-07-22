import { useEffect, useState } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { api } from './api';
import { useAuth } from './auth';
import Welcome from './screens/Welcome';
import Home from './screens/Home';
import Journal from './screens/Journal';
import Ask from './screens/Ask';
import Alerts from './screens/Alerts';
import Actions from './screens/Actions';
import MemoryBook from './screens/MemoryBook';
import Me from './screens/Me';

const NAV = [
  { to: '/', icon: '🏡', label: 'Home' },
  { to: '/journal', icon: '📓', label: 'Journal' },
  { to: '/ask', icon: '💬', label: 'Ask' },
  { to: '/alerts', icon: '🔔', label: 'Alerts' },
  { to: '/actions', icon: '🎁', label: 'Actions' },
  { to: '/memory', icon: '📖', label: 'Memory' },
  { to: '/me', icon: '🪞', label: 'Me' },
];

export default function App() {
  const { user } = useAuth();
  const location = useLocation();
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    if (!user) return undefined;
    let alive = true;
    async function poll() {
      try {
        const alerts = await api.get('/alerts');
        if (alive) setAlertCount(alerts.filter((a) => a.status === 'new').length);
      } catch { /* quiet */ }
    }
    poll();
    const timer = setInterval(poll, 30000);
    return () => { alive = false; clearInterval(timer); };
  }, [user, location.pathname]);

  if (!user) return <Welcome />;

  return (
    <div className="app-shell">
      <header className="row between" style={{ marginBottom: 'var(--space-3)' }}>
        <span className="brand">Aangan<span className="hindi">आँगन</span></span>
        <span className="muted">{user.name}</span>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/actions" element={<Actions />} />
        <Route path="/memory" element={<MemoryBook />} />
        <Route path="/me" element={<Me />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <nav className="bottom-nav" aria-label="Main navigation">
        {NAV.map(({ to, icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
            <span className="icon" aria-hidden="true">{icon}</span>
            {label}
            {to === '/alerts' && alertCount > 0 && <span className="badge">{alertCount}</span>}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
