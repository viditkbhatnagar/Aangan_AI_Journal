import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';

export default function Home() {
  const { user, members } = useAuth();
  const [nudges, setNudges] = useState([]);
  const others = members.filter((m) => m.id !== user.id);

  useEffect(() => {
    api.get('/nudges').then(setNudges).catch(() => setNudges([]));
  }, []);

  return (
    <div className="stack-lg">
      <section>
        <h1>Namaste, {user.name}</h1>
        <p className="muted">This courtyard is yours. Speak whenever you like — everything stays private unless you share it.</p>
      </section>

      <Link to="/journal" style={{ textDecoration: 'none', display: 'block' }}>
        <div className="talk-frame">
          <span className="talk-button" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            Talk to me
          </span>
          <p className="muted" style={{ marginTop: 'var(--space-2)' }}>Ten seconds or ten minutes — it's all yours.</p>
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
        <h2>Your circle</h2>
        {others.length === 0 ? (
          <p className="muted" style={{ marginTop: 'var(--space-2)' }}>
            No one else here yet — share your invite code so family can join.
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
