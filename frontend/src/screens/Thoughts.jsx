import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';
import MoodStrip from '../components/MoodStrip';
import { Inkwell, LampIcon, LockIcon, MirrorIcon } from '../icons';

// split prose into "ink lines" (sentences) that write themselves in
function inkLines(text) {
  return text.split(/(?<=[.!?…।])\s+/).filter(Boolean);
}

const PERSONAL_KINDS = ['personal_date', 'open_plan'];

export default function Thoughts() {
  const { user } = useAuth();
  const lang = user.language;
  const [data, setData] = useState(null);
  const [personalNudges, setPersonalNudges] = useState([]);
  const [dismissed, setDismissed] = useState([]); // client-side hide (pilot)
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get('/thoughts').then(setData).catch((e) => setError(e.message));
    api.get('/nudges')
      .then((all) => setPersonalNudges(all.filter((n) => PERSONAL_KINDS.includes(n.kind))))
      .catch(() => setPersonalNudges([]));
  }, []);

  const empty = data && data.mirror.total_entries === 0;

  return (
    <div className="stack-lg">
      <section className="screen-head">
        <div className="meta">Private · sealed</div>
        <h1>{t(lang, 'thoughts.title')}</h1>
        <p>{t(lang, 'thoughts.subtitle')}</p>
      </section>

      {error && <p className="error-text" role="alert">{error}</p>}

      {/* the same personal nudges as Home — the journal remembering for you */}
      {personalNudges.filter((n) => !dismissed.includes(n.text)).map((n, i) => (
        <div key={i} className="stickynote">
          <span className="pin" aria-hidden="true"></span>
          <div className="meta" style={{ color: 'var(--red-ink)', marginBottom: 6 }} className="iconline"><LampIcon /> Your journal remembers</div>
          <p>{n.text}</p>
          {n.kind === 'personal_date' && (
            <div style={{ marginTop: 12 }}>
              <button className="quiet" onClick={() => setDismissed((d) => [...d, n.text])}>
                {t(lang, 'nudge.noted')}
              </button>
            </div>
          )}
        </div>
      ))}

      {empty ? (
        <div className="empty-state">
          <span className="big" aria-hidden="true"><MirrorIcon /></span>
          {t(lang, 'thoughts.empty')}
        </div>
      ) : (
        <>
          {/* the weekly reflection — a hand-written note at the top */}
          {data && (
            <div className="note reveal">
              <div className="note-by"><Inkwell /><span className="meta">{t(lang, 'thoughts.reflection')}</span></div>
              <p className="reply">
                {inkLines(data.reflection).map((line, i) => (
                  <span key={i} className="ink-line" style={{ '--i': i }}>{line}</span>
                ))}
              </p>
            </div>
          )}

          {/* the mirror: streak, entries, mood, themes */}
          <section className="card stack">
            <div className="card-title" style={{ marginBottom: 0 }}>
              <h2>{t(lang, 'thoughts.mirror')}</h2>
              <span className="private-tag"><LockIcon /> Only you</span>
            </div>
            {data && (
              <>
                <div className="row" style={{ gap: 'var(--space-4)' }}>
                  <div><strong style={{ fontSize: '1.4rem' }}>{data.mirror.total_entries}</strong><p className="muted">{t(lang, 'thoughts.entries')}</p></div>
                  <div><strong style={{ fontSize: '1.4rem' }}>{data.mirror.streak_days}</strong><p className="muted">{t(lang, 'thoughts.streak')}</p></div>
                </div>
                <MoodStrip series={data.mirror.mood_series} />
                {data.mirror.themes.length > 0 && (
                  <div className="row" style={{ flexWrap: 'wrap' }}>
                    {data.mirror.themes.map((th) => (
                      <span key={th.name} className="pill">{th.name} · {th.count}</span>
                    ))}
                  </div>
                )}
              </>
            )}
          </section>

          {/* open loops — margin-notes with their source quotes */}
          {data?.open_loops.length > 0 && (
            <section className="card stack">
              <h2>{t(lang, 'thoughts.loops')}</h2>
              {data.open_loops.map((loop) => (
                <div key={loop.fact_id} className="mnote">
                  <span className="k">
                    plan · {loop.age_days === 0 ? 'today' : `${loop.age_days}d ago`}
                  </span>
                  <span className="v">{loop.content}</span>
                  {loop.source_quote && loop.source_quote !== loop.content && (
                    <p className="muted" style={{ fontSize: '0.85rem', marginTop: 2 }}>“{loop.source_quote}”</p>
                  )}
                </div>
              ))}
            </section>
          )}

          {/* coming up — small postmarked date chips */}
          {data?.upcoming.length > 0 && (
            <section className="card stack">
              <h2>{t(lang, 'thoughts.upcoming')}</h2>
              <div className="row" style={{ flexWrap: 'wrap', gap: '10px' }}>
                {data.upcoming.map((u) => (
                  <span key={u.fact_id} className="row" style={{ width: 'auto', gap: '8px', alignItems: 'center' }}>
                    <span className="postmark">
                      {new Date(`${u.date}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
                    </span>
                    <span className="pill">
                      {u.days_away === 0 ? '· today' : u.days_away === 1 ? '· tomorrow' : `· in ${u.days_away} days`}
                    </span>
                    <span style={{ fontFamily: 'var(--serif)', fontStyle: 'italic' }}>{u.content}</span>
                  </span>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
