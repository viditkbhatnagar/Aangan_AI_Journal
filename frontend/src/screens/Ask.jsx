import { useState } from 'react';
import { api } from '../api';
import { t } from '../i18n';
import { useAuth } from '../auth';
import HoldToTalk from '../components/HoldToTalk';
import UpgradeCard from '../components/UpgradeCard';
import { speak, stopSpeaking } from '../voice';
import { Inkwell } from '../icons';

function ReportButton({ subjectKind, subjectId = null, context }) {
  const [sent, setSent] = useState(false);
  if (sent) return <span className="meta">noted 🙏</span>;
  return (
    <button
      className="quiet"
      title="This looks wrong — tell a human"
      aria-label="Report this"
      onClick={async () => {
        await api.post('/feedback', {
          kind: 'report', subject_kind: subjectKind, subject_id: subjectId,
          message: context.slice(0, 3000),
        });
        setSent(true);
      }}
    >
      🚩
    </button>
  );
}

// split prose into "ink lines" (sentences) that write themselves in
function inkLines(text) {
  return text.split(/(?<=[.!?…])\s+/).filter(Boolean);
}

function ReadAloud({ answer, language }) {
  const [playing, setPlaying] = useState(false);
  async function toggle() {
    if (playing) {
      stopSpeaking();
      setPlaying(false);
      return;
    }
    setPlaying(true);
    await speak(answer, language, { warm: true });
    // the browser can't tell us exactly when Aura audio ends here, so relax after a while
    setTimeout(() => setPlaying(false), Math.min(30000, answer.length * 90));
  }
  return (
    <button className={`readaloud ${playing ? 'on' : ''}`} aria-pressed={playing} onClick={toggle}>
      <span aria-hidden="true">🔊</span>
      <span className="wave" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
      {playing ? 'Reading…' : 'Read aloud'}
    </button>
  );
}

// The Companion's answer, penned back like a returned note.
function CompanionNote({ turn }) {
  const [showSrc, setShowSrc] = useState(false);
  const lines = inkLines(turn.answer);
  return (
    <div className="note reveal">
      <div className="note-by"><Inkwell /><span className="meta">The Companion writes back</span></div>
      <p className="reply">
        {lines.map((line, i) => (
          <span key={i} className="ink-line" style={{ '--i': i }}>{line}</span>
        ))}
      </p>
      <div className="note-foot">
        <ReadAloud answer={turn.answer} language={turn.language} />
        {turn.snippets?.length > 0 && (
          <button className="src-btn" aria-expanded={showSrc} onClick={() => setShowSrc(!showSrc)}>
            {showSrc ? '▾' : '▸'} From {turn.snippets.length} shared moment{turn.snippets.length > 1 ? 's' : ''}
          </button>
        )}
        <ReportButton subjectKind="answer" context={`Q: ${turn.question}\nA: ${turn.answer}`} />
      </div>
      {showSrc && turn.snippets?.map((s, j) => (
        <div key={j} className="src">
          <div className="meta">{s.author_name} · {new Date(s.created_at).toLocaleDateString()}</div>
          <p>“{s.text}”</p>
        </div>
      ))}
    </div>
  );
}

export default function Ask() {
  const { user } = useAuth();
  const [question, setQuestion] = useState('');
  const [thread, setThread] = useState([]); // {question, answer, snippets}
  const [busy, setBusy] = useState(false);
  const [pendingQ, setPendingQ] = useState(null);
  const [error, setError] = useState(null);
  const [capMessage, setCapMessage] = useState(null);

  async function askWith(payload, label) {
    setBusy(true);
    setPendingQ(label);
    setError(null);
    try {
      const result = payload instanceof FormData
        ? await api.postForm('/ask', payload)
        : await api.post('/ask', payload);
      setThread((t) => [{ question: label, ...result }, ...t]);
      speak(result.answer, result.language, { warm: true });
      setQuestion('');
    } catch (err) {
      if (err.status === 402) setCapMessage(err.message);
      else setError(err.message);
    } finally {
      setBusy(false);
      setPendingQ(null);
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
      <section className="screen-head">
        <div className="meta">The Companion</div>
        <h1>{t(user.language, 'ask.title')}</h1>
        <p>{t(user.language, 'ask.subtitle')}</p>
      </section>

      <section className="card">
        <form className="ask-bar" onSubmit={onSubmit}>
          <span className="inp">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={user.language === 'hi' ? 'जैसे: दीपा का दिन कैसा था?' : "e.g. How was Deepa's day?"}
              aria-label="Your question"
            />
          </span>
          <button disabled={busy || !question.trim()}>{busy ? '…' : t(user.language, 'ask.button')}</button>
        </form>
        <div style={{ marginTop: 12 }}>
          <HoldToTalk onRecorded={onRecorded} disabled={busy} label="Ask by voice" />
        </div>
      </section>

      {capMessage && <UpgradeCard message={capMessage} onDismiss={() => setCapMessage(null)} />}
      {error && <p className="error-text" role="alert">{error}</p>}

      <div className="thread" aria-live="polite">
        {busy && (
          <div className="qa">
            {pendingQ && (
              <div className="you-q">
                <div className="meta">✎ You asked</div>
                <p>“{pendingQ}”</p>
              </div>
            )}
            <div className="thinking" role="status">
              <Inkwell />
              dipping the nib <span className="dots" aria-hidden="true"><i>.</i><i>.</i><i>.</i></span>
            </div>
          </div>
        )}
        {thread.map((turn, i) => (
          <div key={i} className="qa">
            <div className="you-q">
              <div className="meta">✎ You asked</div>
              <p>“{turn.question}”</p>
            </div>
            <CompanionNote turn={turn} />
          </div>
        ))}
      </div>
      {thread.length > 0 && (
        <div style={{ textAlign: 'center' }}>
          <button className="quiet" onClick={stopSpeaking}>Stop speaking</button>
        </div>
      )}
    </div>
  );
}
