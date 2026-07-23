import { useState } from 'react';
import { api } from '../api';

// Shown when a free-plan cap is reached (HTTP 402). One gentle card — never a
// wall of upsells.
export default function UpgradeCard({ message, onDismiss }) {
  const [joined, setJoined] = useState(false);

  async function notifyMe() {
    const { message: reply } = await api.post('/plus/interest');
    setJoined(reply);
  }

  return (
    <section className="card stack" style={{ borderColor: 'var(--color-accent)' }} role="status">
      <p>🪔 {message}</p>
      {joined ? (
        <p className="muted">{joined}</p>
      ) : (
        <div className="row">
          <button onClick={notifyMe}>Aangan Plus — notify me</button>
          {onDismiss && <button className="quiet" onClick={onDismiss}>Maybe later</button>}
        </div>
      )}
    </section>
  );
}
