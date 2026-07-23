import { useEffect, useState } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { api } from './api';
import { useAuth } from './auth';
import Welcome from './screens/Welcome';
import ResetPassword from './screens/ResetPassword';
import Home from './screens/Home';
import Journal from './screens/Journal';
import Ask from './screens/Ask';
import Alerts from './screens/Alerts';
import Actions from './screens/Actions';
import { t } from './i18n';
import MemoryBook from './screens/MemoryBook';
import Me from './screens/Me';
import AgentPanel from './components/AgentPanel';

const NAV = [
  { to: '/', icon: '🏡', key: 'nav.home' },
  { to: '/journal', icon: '📓', key: 'nav.journal' },
  { to: '/ask', icon: '💬', key: 'nav.ask' },
  { to: '/alerts', icon: '🔔', key: 'nav.alerts' },
  { to: '/actions', icon: '🎁', key: 'nav.actions' },
  { to: '/memory', icon: '📖', key: 'nav.memory' },
  { to: '/me', icon: '🪞', key: 'nav.me' },
];

export default function App() {
  const { user } = useAuth();
  const location = useLocation();
  const [alertCount, setAlertCount] = useState(0);
  const [panelOpen, setPanelOpen] = useState(false);

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

  if (!user) {
    return location.pathname === '/reset' ? <ResetPassword /> : <Welcome />;
  }

  return (
    <div className="app-shell">
      <header className="row between" style={{ marginBottom: 'var(--space-3)' }}>
        <span className="brand">Aangan<span className="hindi">आँगन</span></span>
        <span className="row" style={{ width: 'auto' }}>
          <button
            className="quiet"
            onClick={() => setPanelOpen(!panelOpen)}
            aria-pressed={panelOpen}
            title="See which agents are working"
          >
            ⚙️ Agents
          </button>
          <span className="muted">{user.name}</span>
        </span>
      </header>
      <AgentPanel open={panelOpen} onClose={() => setPanelOpen(false)} />
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
        {NAV.map(({ to, icon, key }) => (
          <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
            <span className="icon" aria-hidden="true">{icon}</span>
            {t(user.language, key)}
            {to === '/alerts' && alertCount > 0 && <span className="badge">{alertCount}</span>}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
