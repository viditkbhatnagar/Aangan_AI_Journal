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
import {
  ActionsIcon, AlertsIcon, AskIcon, GearIcon, HomeIcon, JournalIcon, MeIcon, MemoryIcon,
} from './icons';

const NAV = [
  { to: '/', Icon: HomeIcon, key: 'nav.home' },
  { to: '/journal', Icon: JournalIcon, key: 'nav.journal' },
  { to: '/ask', Icon: AskIcon, key: 'nav.ask' },
  { to: '/alerts', Icon: AlertsIcon, key: 'nav.alerts' },
  { to: '/actions', Icon: ActionsIcon, key: 'nav.actions' },
  { to: '/memory', Icon: MemoryIcon, key: 'nav.memory' },
  { to: '/me', Icon: MeIcon, key: 'nav.me' },
];

export default function App() {
  const { user, circles, activeCircleId, switchCircle } = useAuth();
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
  }, [user, location.pathname, activeCircleId]);

  if (!user) {
    return location.pathname === '/reset' ? <ResetPassword /> : <Welcome />;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <span className="brand">Aangan<span className="hindi" lang="hi">आँगन</span></span>
        <span className="row" style={{ width: 'auto' }}>
          {circles.length > 1 && (
            <select
              aria-label="Active family circle"
              value={activeCircleId ?? ''}
              onChange={(e) => switchCircle(Number(e.target.value))}
              style={{ width: 'auto', padding: '0.3rem 0.5rem', fontFamily: 'var(--mono)', fontSize: '0.72rem' }}
            >
              {circles.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          )}
          <button
            className="agents-btn"
            onClick={() => setPanelOpen(!panelOpen)}
            aria-pressed={panelOpen}
            title="See which agents are working"
          >
            <GearIcon /> Agents
          </button>
          <span className="user-chip">
            <span className="av" aria-hidden="true">{user.name.charAt(0)}</span>
            {user.name}
          </span>
        </span>
      </header>
      <AgentPanel open={panelOpen} onClose={() => setPanelOpen(false)} />
      <Routes key={activeCircleId ?? 'none'}>
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
        <div className="dock-inner">
          {NAV.map(({ to, Icon, key }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
              <Icon />
              {t(user.language, key)}
              {to === '/alerts' && alertCount > 0 && <span className="badge">{alertCount}</span>}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
