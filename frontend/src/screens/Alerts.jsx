import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';

export default function Alerts() {
  const { user } = useAuth();
  const lang = user.language;
  const [alerts, setAlerts] = useState([]);
  const navigate = useNavigate();

  const refresh = useCallback(async () => setAlerts(await api.get('/alerts')), []);
  useEffect(() => { refresh(); }, [refresh]);

  async function setStatus(alert, status) {
    await api.post(`/alerts/${alert.id}/status`, { status });
    await refresh();
  }

  async function actOn(alert) {
    await setStatus(alert, 'acted');
    navigate('/actions', { state: { alertId: alert.id, suggestion: alert.suggested_action } });
  }

  const fresh = alerts.filter((a) => a.status === 'new' || a.status === 'seen');
  const past = alerts.filter((a) => a.status !== 'new' && a.status !== 'seen');

  return (
    <div className="stack-lg">
      <section className="screen-head">
        <div className="meta">Care nudges</div>
        <h1>{t(lang, 'alerts.title')}</h1>
        <p>{t(lang, 'alerts.subtitle')}</p>
      </section>

      {fresh.length === 0 && (
        <div className="empty-state">
          <span className="big" aria-hidden="true">🌿</span>
          {t(lang, 'alerts.empty')}
        </div>
      )}

      {fresh.map((alert, i) => (
        <article key={alert.id} className="telegram" style={{ opacity: alert.status === 'seen' ? 0.68 : 1 }}>
          <span className={`tg-stamp ${alert.severity}`} aria-hidden="true">{alert.severity}</span>
          <div className="tg-perf top" aria-hidden="true"></div>
          <div className="tg-masthead">
            <span className="tg-mark">Ghar Telegraph</span>
            <span className="tg-no">
              No. {String(alert.id).padStart(3, '0')} · {new Date(alert.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
            </span>
          </div>
          <div className="tg-body">
            <div className="tg-line">From <b>a care wish</b> — delivered to {user.name}</div>
            <p className="alert-msg">{alert.message}</p>
            {alert.suggested_action && (
              <div className="suggested">
                <div className="meta">Suggested</div>
                <p>{alert.suggested_action}</p>
              </div>
            )}
            <div className="alert-actions">
              <button onClick={() => actOn(alert)}>{t(lang, 'alerts.act')}</button>
              {alert.status === 'new' && (
                <button className="ghost" onClick={() => setStatus(alert, 'seen')}>{t(lang, 'alerts.seen')}</button>
              )}
              <button className="ghost" onClick={() => setStatus(alert, 'dismissed')}>{t(lang, 'alerts.dismiss')}</button>
              <button
                className="quiet"
                title="This looks wrong — tell a human"
                onClick={async () => {
                  await api.post('/feedback', {
                    kind: 'report', subject_kind: 'alert', subject_id: alert.id,
                    message: alert.message,
                  });
                  setStatus(alert, 'seen');
                }}
              >
                🚩
              </button>
            </div>
          </div>
          <div className="tg-perf" aria-hidden="true"></div>
        </article>
      ))}

      {past.length > 0 && (
        <details className="trace">
          <summary className="trace-summary">Earlier <span className="trace-count">{past.length}</span></summary>
          <div className="stack" style={{ marginTop: 'var(--space-2)' }}>
            {past.map((alert) => (
              <article key={alert.id} className="card row between">
                <span className="muted">{alert.message}</span>
                <span className="pill">{alert.status}</span>
              </article>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
