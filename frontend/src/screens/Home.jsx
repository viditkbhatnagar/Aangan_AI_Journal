import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';

export default function Home() {
  const { user, members } = useAuth();
  const [nudges, setNudges] = useState([]);
  const [circle, setCircle] = useState(null);
  const [copied, setCopied] = useState(false);
  const others = members.filter((m) => m.id !== user.id);

  useEffect(() => {
    api.get('/nudges').then(setNudges).catch(() => setNudges([]));
    api.get('/circles/mine').then(setCircle).catch(() => setCircle(null));
  }, []);

  async function copyInvite() {
    try {
      await navigator.clipboard.writeText(circle.invite_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard unavailable */ }
  }

  return (
    <div className="stack-lg">
      <section>
        <h1>{t(user.language, 'home.greeting')}, {user.name}</h1>
        <p className="muted">{t(user.language, 'home.subtitle')}</p>
      </section>

      <Link to="/journal" style={{ textDecoration: 'none', display: 'block' }}>
        <div className="talk-frame">
          <span className="talk-button" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            {t(user.language, 'home.talk')}
          </span>
          <p className="muted" style={{ marginTop: 'var(--space-2)' }}>{t(user.language, 'home.talk.hint')}</p>
        </div>
      </Link>

      {nudges.length > 0 && (
        <section className="stack" aria-label="Gentle nudges">
          {nudges.map((n, i) => (
            <div key={i} className="card row" style={{ alignItems: 'flex-start' }}>
              <p className="grow">{n.text}</p>
              {n.kind === 'journal' && <Link className="btn" to="/journal" style={{ textDecoration: 'none' }}>Journal</Link>}
              {n.kind === 'upcoming_date' && <Link className="btn" to="/actions" style={{ textDecoration: 'none' }}>Prepare</Link>}
            </div>
          ))}
        </section>
      )}

      <section className="card">
        <div className="row between">
          <h2>{t(user.language, 'home.circle')}{circle ? ` — ${circle.name}` : ''}</h2>
          {circle && (
            <button className="quiet" onClick={copyInvite} title="Copy the invite code for family to join">
              {copied ? 'Copied ✓' : `Invite: ${circle.invite_code} ⧉`}
            </button>
          )}
        </div>
        {others.length === 0 ? (
          <p className="muted" style={{ marginTop: 'var(--space-2)' }}>
            {t(user.language, 'home.circle.empty')}
          </p>
        ) : (
          <ul style={{ listStyle: 'none', marginTop: 'var(--space-2)' }} className="stack">
            {others.map((m) => (
              <li key={m.id} className="row between">
                <span>{m.name}</span>
                {m.relationship_label && <span className="pill">{m.relationship_label}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
