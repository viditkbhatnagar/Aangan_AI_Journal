import { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';
import HoldToTalk from '../components/HoldToTalk';
import { speak, stopSpeaking } from '../voice';

export default function Ask() {
  const { user } = useAuth();
  const [question, setQuestion] = useState('');
  const [thread, setThread] = useState([]); // {question, answer, snippets}
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function askWith(payload, label) {
    setBusy(true);
    setError(null);
    try {
      const result = payload instanceof FormData
        ? await api.postForm('/ask', payload)
        : await api.post('/ask', payload);
      setThread((t) => [{ question: label, ...result }, ...t]);
      speak(result.answer, result.language);
      setQuestion('');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    if (!question.trim()) return;
    askWith({ question: question.trim() }, question.trim());
  }

  function onRecorded(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'question.webm');
    askWith(formData, '🎙 (spoken question)');
  }

  return (
    <div className="stack-lg">
      <section>
        <h1>Ask the Companion</h1>
        <p className="muted">
          Ask about your family — it answers only from what they chose to share with you.
        </p>
      </section>

      <form className="card row" onSubmit={onSubmit}>
        <input
          className="grow"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={user.language === 'hi' ? 'जैसे: दीपा का दिन कैसा था?' : "e.g. How was Deepa's day?"}
          aria-label="Your question"
        />
        <button disabled={busy || !question.trim()}>{busy ? '…' : 'Ask'}</button>
      </form>

      <HoldToTalk onRecorded={onRecorded} disabled={busy} />
      {error && <p className="error-text" role="alert">{error}</p>}

      {thread.map((turn, i) => (
        <article key={i} className="card stack">
          <p className="muted">You asked: {turn.question}</p>
          <div className="row between" style={{ alignItems: 'flex-start' }}>
            <p style={{ fontSize: '1.05rem' }}>{turn.answer}</p>
            <button className="quiet" onClick={() => speak(turn.answer, turn.language)} aria-label="Read aloud">
              🔊
            </button>
          </div>
          {turn.snippets?.length > 0 && (
            <details>
              <summary className="muted">From {turn.snippets.length} shared moment{turn.snippets.length > 1 ? 's' : ''}</summary>
              <ul className="stack" style={{ listStyle: 'none', marginTop: 'var(--space-1)' }}>
                {turn.snippets.map((s, j) => (
                  <li key={j} className="muted">
                    “{s.text}” — {s.author_name}, {new Date(s.created_at).toLocaleDateString()}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </article>
      ))}
      {thread.length > 0 && (
        <div style={{ textAlign: 'center' }}>
          <button className="quiet" onClick={stopSpeaking}>Stop speaking</button>
        </div>
      )}
    </div>
  );
}
