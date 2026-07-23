import { useState } from 'react';
import { api, setToken } from '../api';

// Reached via a one-time link the circle admin generates (pilot recovery flow).
export default function ResetPassword() {
  const token = new URLSearchParams(window.location.search).get('token') || '';
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    try {
      const { access_token } = await api.post('/auth/reset', { token, new_password: password });
      setToken(access_token);
      setDone(true);
      setTimeout(() => { window.location.href = '/'; }, 1200);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="app-shell" style={{ paddingTop: 'var(--space-5)' }}>
      <div style={{ textAlign: 'center', marginBottom: 'var(--space-4)' }}>
        <h1>Set a new password</h1>
        <p className="muted">Choose something only you would know.</p>
      </div>
      {done ? (
        <p className="card" style={{ textAlign: 'center' }}>All set — taking you home. 🪔</p>
      ) : (
        <form className="card stack" onSubmit={submit}>
          <div>
            <label htmlFor="newpass">New password (8+ characters)</label>
            <input
              id="newpass" type="password" minLength={8} required
              value={password} onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="error-text" role="alert">{error}</p>}
          <button disabled={password.length < 8}>Save and come in</button>
        </form>
      )}
    </main>
  );
}
