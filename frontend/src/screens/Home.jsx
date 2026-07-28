import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';
import { Diya } from '../icons';

export default function Home() {
  const { user, members } = useAuth();
  const navigate = useNavigate();
  const [nudges, setNudges] = useState([]);
  const [dismissed, setDismissed] = useState([]); // client-side hide (pilot)
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
      <section className="greet">
        <h1>{t(user.language, 'home.greeting')}, {user.name}</h1>
        <p>{t(user.language, 'home.subtitle')}</p>
      </section>

      {/* the lit diya — tap to go speak */}
      <section className="orb-stage">
        <button
          type="button"
          className="orb-btn"
          onClick={() => navigate('/journal')}
          aria-label={`${t(user.language, 'home.talk')} — open your journal to record`}
        >
          <span className="orb-glow" aria-hidden="true"></span>
          <span className="ripple" aria-hidden="true"></span>
          <span className="ripple r2" aria-hidden="true"></span>
          <Diya />
        </button>
        <div className="orb-label">{t(user.language, 'home.talk')}</div>
        <div className="orb-sub">{t(user.language, 'home.talk.hint')}</div>
      </section>

      {nudges.filter((n) => !dismissed.includes(n.text)).length > 0 && (
        <section className="stack" aria-label="Gentle nudges">
          {/* personal_date / open_plan come from the Personal Radar — the
              author's own journal remembering FOR them. Real timed delivery
              (a Thursday-night push) needs a push channel that doesn't exist
              yet; showing them on next open is the pilot behavior, not a bug. */}
          {nudges.filter((n) => !dismissed.includes(n.text)).map((n, i) => {
            const personal = n.kind === 'personal_date' || n.kind === 'open_plan';
            return (
              <div key={i} className="stickynote">
                <span className="pin" aria-hidden="true"></span>
                <div className="meta" style={{ color: 'var(--red-ink)', marginBottom: 6 }}>
                  {personal ? '🪔 Your journal remembers' : 'A gentle nudge'}
                </div>
                <p>{n.text}</p>
                <div style={{ marginTop: 12 }}>
                  {n.kind === 'journal' && <Link className="btn" to="/journal" style={{ borderBottom: 'none' }}>Journal</Link>}
                  {n.kind === 'upcoming_date' && <Link className="btn" to="/actions" style={{ borderBottom: 'none' }}>Prepare</Link>}
                  {n.kind === 'personal_date' && (
                    <button className="quiet" onClick={() => setDismissed((d) => [...d, n.text])}>
                      {t(user.language, 'nudge.noted')}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </section>
      )}

      <section className="card">
        <div className="card-title">
          <h2>{t(user.language, 'home.circle')}{circle ? ` — ${circle.name}` : ''}</h2>
          {circle && (
            <button
              type="button"
              className="invite-stamp"
              onClick={copyInvite}
              title="Copy the invite code for family to join"
              style={{ background: copied ? 'rgba(62,110,112,0.16)' : undefined, cursor: 'pointer', boxShadow: 'none' }}
            >
              <span className="is-k">{copied ? 'Copied ✓' : 'Invite'}</span>
              <span className="is-v">{circle.invite_code}</span>
            </button>
          )}
        </div>
        {others.length === 0 ? (
          <p className="muted" style={{ marginTop: 'var(--space-2)' }}>
            {t(user.language, 'home.circle.empty')}
          </p>
        ) : (
          <>
            <p className="meta" style={{ marginBottom: 6 }}>The family register · {others.length} name{others.length > 1 ? 's' : ''} in ink</p>
            <div className="reg-book">
              {others.map((m) => (
                <div key={m.id} className="reg-row">
                  <span className="ini" aria-hidden="true">{m.name.charAt(0)}</span>
                  <span className="nm">{m.name}</span>
                  {m.relationship_label && <span className="rel">{m.relationship_label}</span>}
                </div>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
