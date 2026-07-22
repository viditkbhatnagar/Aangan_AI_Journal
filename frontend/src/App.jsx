import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './auth';
import Welcome from './screens/Welcome';
import Home from './screens/Home';
import Journal from './screens/Journal';

const NAV = [
  { to: '/', icon: '🏡', label: 'Home' },
  { to: '/journal', icon: '📓', label: 'Journal' },
];

export default function App() {
  const { user } = useAuth();

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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <nav className="bottom-nav" aria-label="Main navigation">
        {NAV.map(({ to, icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
            <span className="icon" aria-hidden="true">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
