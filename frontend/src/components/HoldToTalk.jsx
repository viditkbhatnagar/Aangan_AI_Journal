import { useRef, useState } from 'react';
import { startRecording } from '../voice';

const MAX_RECORDING_MS = 5 * 60 * 1000; // soft cost cap; Plus can raise it later

// Big hold-to-talk button. Hold to record; release to send the blob up.
export default function HoldToTalk({ onRecorded, disabled }) {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState(null);
  const sessionRef = useRef(null);
  const timerRef = useRef(null);

  async function begin(e) {
    e.preventDefault();
    if (disabled || recording) return;
    setError(null);
    try {
      sessionRef.current = await startRecording();
      setRecording(true);
      timerRef.current = setTimeout(() => {
        setError('That was a lovely long one — I kept the first five minutes.');
        end();
      }, MAX_RECORDING_MS);
    } catch {
      setError("I couldn't reach your microphone — you can type instead.");
    }
  }

  async function end() {
    if (!sessionRef.current) return;
    clearTimeout(timerRef.current);
    const session = sessionRef.current;
    sessionRef.current = null;
    setRecording(false);
    const blob = await session.stop();
    if (blob.size > 0) onRecorded(blob);
  }

  return (
    <div className="talk-frame">
      <button
        type="button"
        className={`talk-button ${recording ? 'recording' : ''}`}
        onPointerDown={begin}
        onPointerUp={end}
        onPointerLeave={() => recording && end()}
        disabled={disabled}
        aria-pressed={recording}
      >
        {recording ? 'Listening…' : 'Hold to talk'}
      </button>
      <p className="muted" style={{ marginTop: 'var(--space-2)' }}>
        {recording ? 'Let go when you are done.' : 'Press and hold, speak freely.'}
      </p>
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
