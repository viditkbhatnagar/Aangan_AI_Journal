import { useAuth } from '../auth';

export default function Home() {
  const { user, members } = useAuth();
  const others = members.filter((m) => m.id !== user.id);

  return (
    <div className="stack-lg">
      <section>
        <h1>Namaste, {user.name}</h1>
        <p className="muted">This courtyard is yours. Speak whenever you like — everything stays private unless you share it.</p>
      </section>

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
