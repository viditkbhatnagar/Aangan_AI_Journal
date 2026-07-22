import { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';

// Share toggles for an entry or one fact: keep private, share with everyone,
// or share with chosen people. Only ever shown to the author.
export default function ShareControls({ entryId, factId = null, current, onChanged }) {
  const { user, members } = useAuth();
  const others = members.filter((m) => m.id !== user.id);
  const [picking, setPicking] = useState(false);
  const [chosen, setChosen] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function setVisibility(visibility, viewerIds = null) {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/entries/${entryId}/share`, {
        fact_id: factId,
        visibility,
        viewer_ids: viewerIds,
      });
      setPicking(false);
      setChosen([]);
      onChanged?.(visibility);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack" style={{ marginTop: 'var(--space-1)' }}>
      <div className="row" style={{ flexWrap: 'wrap' }}>
        <span className={`pill ${current}`}>{current}</span>
        {current !== 'private' && (
          <button className="quiet" disabled={busy} onClick={() => setVisibility('private')}>
            Make private
          </button>
        )}
        {current !== 'circle' && (
          <button className="quiet" disabled={busy} onClick={() => setVisibility('circle')}>
            Share with everyone
          </button>
        )}
        <button className="quiet" disabled={busy || others.length === 0} onClick={() => setPicking(!picking)}>
          Share with chosen…
        </button>
      </div>
      {picking && (
        <div className="row" style={{ flexWrap: 'wrap' }}>
          {others.map((m) => (
            <label key={m.id} className="row" style={{ width: 'auto', gap: '0.3rem' }}>
              <input
                type="checkbox"
                style={{ width: 'auto' }}
                checked={chosen.includes(m.id)}
                onChange={(e) =>
                  setChosen(e.target.checked ? [...chosen, m.id] : chosen.filter((id) => id !== m.id))
                }
              />
              {m.name}
            </label>
          ))}
          <button disabled={busy || chosen.length === 0} onClick={() => setVisibility('custom', chosen)}>
            Share
          </button>
        </div>
      )}
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
