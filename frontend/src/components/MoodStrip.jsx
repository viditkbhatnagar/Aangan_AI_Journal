// The mood-over-time strip — moved out of Me.jsx so My Thoughts owns the
// mirror's guts. Purely presentational; the series is the author's own.
export default function MoodStrip({ series }) {
  if (!series.length) return <p className="muted">Your moods will appear here as you journal.</p>;
  return (
    <div className="row" style={{ alignItems: 'flex-end', gap: '3px', minHeight: '3.5rem', overflowX: 'auto' }} aria-label="Mood over time">
      {series.slice(-30).map((p, i) => {
        const height = 12 + Math.round((p.score + 1) * 20);
        const color = p.score > 0.1 ? 'var(--color-accent)' : p.score < -0.1 ? 'var(--color-rose)' : 'var(--color-line)';
        return (
          <div
            key={i}
            title={`${p.date}: ${p.summary}`}
            style={{ width: '10px', height: `${height}px`, background: color, borderRadius: '4px 4px 0 0', flexShrink: 0 }}
          />
        );
      })}
    </div>
  );
}
