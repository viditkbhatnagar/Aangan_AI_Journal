import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';

const PRESSED = [
  <svg key="a" className="pressed" viewBox="0 0 40 40" aria-hidden="true"><g fill="#b23a2e" opacity=".85"><ellipse cx="20" cy="10" rx="4.5" ry="7" /><ellipse cx="30" cy="20" rx="7" ry="4.5" /><ellipse cx="20" cy="30" rx="4.5" ry="7" /><ellipse cx="10" cy="20" rx="7" ry="4.5" /></g><circle cx="20" cy="20" r="4" fill="#c08a2e" /><path d="M20 30 q2 6 -2 9" stroke="#565633" strokeWidth="1.4" fill="none" /></svg>,
  <svg key="b" className="pressed" viewBox="0 0 40 40" aria-hidden="true"><g fill="#7b7a52" opacity=".8"><ellipse cx="20" cy="11" rx="4" ry="6.5" /><ellipse cx="29" cy="20" rx="6.5" ry="4" /><ellipse cx="20" cy="29" rx="4" ry="6.5" /><ellipse cx="11" cy="20" rx="6.5" ry="4" /></g><circle cx="20" cy="20" r="3.6" fill="#c08a2e" /></svg>,
];

// A shared moment, taped into the family scrapbook.
function Polaroid({ moment, index }) {
  return (
    <article className="polaroid">
      <span className={`tape ${index % 2 === 0 ? 'tl' : 'br'}`} aria-hidden="true"></span>
      {index % 3 === 1 && PRESSED[index % 2]}
      <p className="po-caption">“{moment.text}”</p>
      <div className="keep-foot">
        <span className="keep-by">— {moment.author_name}</span>
        <span className="keep-when">{new Date(moment.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
      </div>
    </article>
  );
}

export default function MemoryBook() {
  const { user } = useAuth();
  const lang = user.language;
  const [book, setBook] = useState(null);

  useEffect(() => {
    api.get('/keepsake').then(setBook).catch(() => setBook({ moments: [], on_this_day: [] }));
  }, []);

  if (!book) return <p className="muted">Opening the memory book…</p>;

  return (
    <div className="stack-lg">
      <section className="screen-head">
        <div className="meta">The keepsake book</div>
        <h1>{t(lang, 'memory.title')}</h1>
        <p>{t(lang, 'memory.subtitle')}</p>
      </section>

      {book.on_this_day.length > 0 && (
        <section>
          <div className="sec-kicker" style={{ textAlign: 'left', marginBottom: 'var(--space-2)' }}>
            <div className="meta">🕯 A year (or more) ago today</div>
          </div>
          <div className="album">
            {book.on_this_day.map((m, i) => <Polaroid key={`otd-${m.entry_id}`} moment={m} index={i} />)}
          </div>
        </section>
      )}

      {book.moments.length === 0 ? (
        <div className="empty-state">
          <span className="big" aria-hidden="true">📖</span>
          The book is waiting for its first shared moment.
        </div>
      ) : (
        <div className="album">
          {book.moments.map((m, i) => <Polaroid key={m.entry_id} moment={m} index={i} />)}
        </div>
      )}
    </div>
  );
}
