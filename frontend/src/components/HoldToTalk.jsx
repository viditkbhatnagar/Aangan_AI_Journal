import { useRef, useState } from 'react';
import { startRecording } from '../voice';
import { NibIcon } from '../icons';

const MAX_RECORDING_MS = 5 * 60 * 1000; // soft cost cap; Plus can raise it later

// Hold-to-record, styled as dipping a nib to write. Release to send the blob up.
export default function HoldToTalk({ onRecorded, disabled, label = 'Dip the nib to speak' }) {
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
    <div>
      <button
        type="button"
        className={`hold ${recording ? 'rec' : ''}`}
        onPointerDown={begin}
        onPointerUp={end}
        onPointerLeave={() => recording && end()}
        disabled={disabled}
        aria-pressed={recording}
      >
        <span className="nib-drop" aria-hidden="true"><NibIcon /></span>
        {recording ? 'Listening — let go when done' : label}
      </button>
      {error && <p className="error-text" style={{ marginTop: 'var(--space-1)' }}>{error}</p>}
    </div>
  );
}
