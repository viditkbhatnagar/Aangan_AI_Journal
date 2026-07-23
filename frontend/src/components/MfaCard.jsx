import { useState } from 'react';
import { api } from '../api';

/** Two-factor enrollment card for the Me screen.
 *  Flow: setup (QR + secret) → confirm a code → enabled. Disable needs a code. */
export default function MfaCard({ user }) {
  const [enabled, setEnabled] = useState(Boolean(user?.mfa_enabled));
  const [setup, setSetup] = useState(null); // {secret, otpauth_uri, qr_svg}
  const [code, setCode] = useState('');
  const [notice, setNotice] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function begin() {
    setError(null);
    setBusy(true);
    try {
      setSetup(await api.post('/auth/mfa/setup', {}));
      setCode('');
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function confirm(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const result = await api.post('/auth/mfa/enable', { code: code.trim() });
      setEnabled(true);
      setSetup(null);
      setNotice(result.message);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function disable(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.post('/auth/mfa/disable', { code: code.trim() });
      setEnabled(false);
      setCode('');
      setNotice('Two-factor is off.');
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <section className="card stack" aria-label="Security">
      <h2>Security</h2>
      {enabled ? (
        <>
          <p className="muted">Two-factor is on — logins ask for a code from your authenticator app.</p>
          <form className="row" onSubmit={disable}>
            <input
              inputMode="numeric"
              placeholder="Code to turn it off"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <button className="ghost" disabled={busy || code.trim().length < 6}>Turn off</button>
          </form>
        </>
      ) : setup ? (
        <>
          <p className="muted">
            Scan this with Google Authenticator, Authy, or any TOTP app — or type the
            secret <code>{setup.secret}</code> by hand. Then enter the 6-digit code it shows.
          </p>
          <img
            alt="QR code for your authenticator app"
            width="180"
            height="180"
            style={{ background: '#fff', borderRadius: '8px', padding: '6px' }}
            src={`data:image/svg+xml;utf8,${encodeURIComponent(setup.qr_svg)}`}
          />
          <form className="row" onSubmit={confirm}>
            <input
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="123456"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <button disabled={busy || code.trim().length < 6}>Confirm & turn on</button>
          </form>
        </>
      ) : (
        <>
          <p className="muted">
            Add a second latch to your account: a 6-digit code from an authenticator
            app at every login.
          </p>
          <button onClick={begin} disabled={busy}>Set up two-factor</button>
        </>
      )}
      {notice && <p className="muted" role="status">{notice}</p>}
      {error && <p className="error-text" role="alert">{error}</p>}
    </section>
  );
}
