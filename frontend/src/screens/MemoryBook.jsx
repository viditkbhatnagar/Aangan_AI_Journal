import { useEffect, useState } from 'react';
import { api } from '../api';

function Moment({ moment }) {
  return (
    <article className="card stack">
      <div className="row between">
        <strong>{moment.author_name}</strong>
        <span className="muted">{new Date(moment.created_at).toLocaleDateString()}</span>
      </div>
      <p>{moment.text}</p>
    </article>
  );
}

export default function MemoryBook() {
  const [book, setBook] = useState(null);

  useEffect(() => {
    api.get('/keepsake').then(setBook).catch(() => setBook({ moments: [], on_this_day: [] }));
  }, []);

  if (!book) return <p className="muted">Opening the memory book…</p>;

  return (
    <div className="stack-lg">
      <section>
        <h1>Memory book</h1>
        <p className="muted">The moments your family chose to share — kept safe, together.</p>
      </section>

      {book.on_this_day.length > 0 && (
        <section className="stack">
          <h2>🕯 A year (or more) ago today</h2>
          {book.on_this_day.map((m) => <Moment key={`otd-${m.entry_id}`} moment={m} />)}
        </section>
      )}

      {book.moments.length === 0 ? (
        <div className="empty-state">
          <span className="big" aria-hidden="true">📖</span>
          The book is waiting for its first shared moment.
        </div>
      ) : (
        <section className="stack">
          {book.moments.map((m) => <Moment key={m.entry_id} moment={m} />)}
        </section>
      )}
    </div>
  );
}
