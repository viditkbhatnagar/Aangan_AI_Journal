import { useEffect, useRef, useState } from 'react';
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
  return text.split(/(?<=[.!?…।])\s+/).filter(Boolean);
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
    // the browser can't tell us exactly when the audio ends here, so relax after a while
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

// One companion turn, penned back like a returned note.
function CompanionNote({ turn, prevQuestion }) {
  const [showSrc, setShowSrc] = useState(false);
  const lines = inkLines(turn.text);
  return (
    <div className="note reveal">
      <div className="note-by"><Inkwell /><span className="meta">The Companion writes back</span></div>
      <p className="reply">
        {lines.map((line, i) => (
          <span key={i} className="ink-line" style={{ '--i': i }}>{line}</span>
        ))}
      </p>
      <div className="note-foot">
        <ReadAloud answer={turn.text} language={turn.language} />
        {turn.snippets?.length > 0 && (
          <button className="src-btn" aria-expanded={showSrc} onClick={() => setShowSrc(!showSrc)}>
            {showSrc ? '▾' : '▸'} From {turn.snippets.length} shared moment{turn.snippets.length > 1 ? 's' : ''}
          </button>
        )}
        <ReportButton subjectKind="answer" context={`Q: ${prevQuestion}\nA: ${turn.text}`} />
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

// survives navigating away and back within one login session (the JWT is
// memory-only, so a hard reload starts a fresh session anyway)
let lastConversationId = null;

export default function Ask() {
  const { user } = useAuth();
  const lang = user.language;
  const [conversationId, setConversationId] = useState(lastConversationId);
  const [turns, setTurns] = useState([]); // {role: user|companion, text, snippets?, language?}
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [capMessage, setCapMessage] = useState(null);
  const endRef = useRef(null);

  // returning to the baithak mid-session: pick the thread back up
  useEffect(() => {
    if (lastConversationId == null) return;
    api.get(`/conversations/${lastConversationId}`)
      .then((c) => setTurns(c.turns.map((tu) => ({ ...tu, language: lang }))))
      .catch(() => { lastConversationId = null; setConversationId(null); });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [turns, busy]);

  async function sendTurn(payload, label) {
    setBusy(true);
    setError(null);
    setTurns((prev) => [...prev, { role: 'user', text: label }]);
    try {
      const result = payload instanceof FormData
        ? await api.postForm('/converse', payload)
        : await api.post('/converse', payload);
      lastConversationId = result.conversation_id;
      setConversationId(result.conversation_id);
      setTurns((prev) => [...prev, {
        role: 'companion', text: result.reply,
        snippets: result.snippets, language: result.language,
      }]);
      speak(result.reply, result.language, { warm: true });
      setMessage('');
    } catch (err) {
      setTurns((prev) => prev.slice(0, -1)); // the turn didn't happen
      if (err.status === 402) setCapMessage(err.message);
      else setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    if (!message.trim() || busy) return;
    sendTurn({ conversation_id: conversationId, message: message.trim() }, message.trim());
  }

  function onRecorded(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'question.webm');
    if (conversationId != null) formData.append('conversation_id', String(conversationId));
    sendTurn(formData, '🎙 (spoken)');
  }

  function newConversation() {
    stopSpeaking();
    lastConversationId = null;
    setConversationId(null);
    setTurns([]);
    setError(null);
  }

  return (
    <div className="stack-lg">
      <section className="screen-head">
        <div className="meta">The Companion</div>
        <h1>{t(lang, 'ask.title')}</h1>
        <p>{t(lang, 'ask.subtitle')}</p>
      </section>

      <div className="thread" aria-live="polite">
        {turns.map((turn, i) => (
          turn.role === 'user' ? (
            <div key={i} className="you-q">
              <div className="meta">✎ You said</div>
              <p>“{turn.text}”</p>
            </div>
          ) : (
            <CompanionNote
              key={i}
              turn={turn}
              prevQuestion={turns[i - 1]?.text ?? ''}
            />
          )
        ))}
        {busy && (
          <div className="thinking" role="status">
            <Inkwell />
            {t(lang, 'ask.thinking')} <span className="dots" aria-hidden="true"><i>.</i><i>.</i><i>.</i></span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {capMessage && <UpgradeCard message={capMessage} onDismiss={() => setCapMessage(null)} />}
      {error && <p className="error-text" role="alert">{error}</p>}

      <section className="card">
        <form className="ask-bar" onSubmit={onSubmit}>
          <span className="inp">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={t(lang, 'ask.placeholder')}
              aria-label="Say something to the Companion"
            />
          </span>
          <button disabled={busy || !message.trim()}>{busy ? '…' : t(lang, 'ask.button')}</button>
        </form>
        <div className="row between" style={{ marginTop: 12, flexWrap: 'wrap' }}>
          <HoldToTalk onRecorded={onRecorded} disabled={busy} label="Talk" />
          <span className="row" style={{ width: 'auto' }}>
            {turns.length > 0 && (
              <button className="quiet" onClick={stopSpeaking}>Stop speaking</button>
            )}
            <button className="quiet" onClick={newConversation}>{t(lang, 'ask.new')}</button>
          </span>
        </div>
      </section>
    </div>
  );
}
