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
      <section>
        <h1>{t(lang, 'alerts.title')}</h1>
        <p className="muted">{t(lang, 'alerts.subtitle')}</p>
      </section>

      {fresh.length === 0 && (
        <div className="empty-state">
          <span className="big" aria-hidden="true">🌿</span>
          {t(lang, 'alerts.empty')}
        </div>
      )}

      {fresh.map((alert) => (
        <article key={alert.id} className="card stack">
          <div className="row between">
            <span className={`pill ${alert.severity}`}>{alert.severity}</span>
            <span className="muted">{new Date(alert.created_at).toLocaleString()}</span>
          </div>
          <p style={{ fontSize: '1.05rem' }}>{alert.message}</p>
          {alert.suggested_action && <p className="muted">💡 {alert.suggested_action}</p>}
          <div className="row">
            <button onClick={() => actOn(alert)}>{t(lang, 'alerts.act')}</button>
            {alert.status === 'new' && (
              <button className="ghost" onClick={() => setStatus(alert, 'seen')}>{t(lang, 'alerts.seen')}</button>
            )}
            <button className="quiet" onClick={() => setStatus(alert, 'dismissed')}>{t(lang, 'alerts.dismiss')}</button>
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
        </article>
      ))}

      {past.length > 0 && (
        <details>
          <summary className="muted">Earlier ({past.length})</summary>
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
