// Inline line-icons for the Chitthi identity — quiet, inked, consistent.

const S = { fill: 'none', 'aria-hidden': true };

export const HomeIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><path d="M4 11.5 12 4l8 7.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /><path d="M6 10.5V20h12v-9.5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" /></svg>
);
export const JournalIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><path d="M6 4h9l4 4v12H6z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /><path d="M9 9h4M9 12.5h6M9 16h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></svg>
);
export const AskIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><path d="M4 5h16v11H8l-4 3.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /><path d="M12 8.4c1.6-1 3 .4 2 1.7-.5.6-1 .8-1 1.6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /><circle cx="13" cy="13.4" r=".9" fill="currentColor" /></svg>
);
export const AlertsIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><path d="M6 10a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /><path d="M10 20a2 2 0 0 0 4 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
);
export const ActionsIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><path d="M4 8.5 12 4l8 4.5v7L12 20l-8-4.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /><path d="M4 8.5 12 13m0 0 8-4.5M12 13v7" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /></svg>
);
export const MemoryIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><rect x="4" y="5" width="16" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.5" /><path d="M4 15l4-3 3 2 3-3 6 4" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" /><circle cx="9" cy="9" r="1.3" stroke="currentColor" strokeWidth="1.3" /></svg>
);
export const MeIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><circle cx="12" cy="8.5" r="3.5" stroke="currentColor" strokeWidth="1.5" /><path d="M5 20a7 7 0 0 1 14 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
);
export const GearIcon = () => (
  <svg viewBox="0 0 24 24" width="15" height="15" {...S}><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" stroke="currentColor" strokeWidth="1.6" /><path d="M19.4 13a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-2.9-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 4.6 13H4a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.1-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 11 3.4V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 2.9 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9H21a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.4.9Z" stroke="currentColor" strokeWidth="1.3" /></svg>
);
export const NibIcon = () => (
  <svg viewBox="0 0 24 24" {...S}><path d="M5 19l4-1 9-9-3-3-9 9-1 4z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" /><path d="M14 6l3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
);
export const MicIcon = () => (
  <svg viewBox="0 0 24 24" width="18" height="18" {...S}><path d="M12 3a2.5 2.5 0 0 0-2.5 2.5v5a2.5 2.5 0 0 0 5 0v-5A2.5 2.5 0 0 0 12 3Z" stroke="currentColor" strokeWidth="1.5" /><path d="M6 10.5a6 6 0 0 0 12 0M12 16.5V20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
);
export const TickIcon = () => (
  <svg viewBox="0 0 24 24" width="20" height="20" {...S}><path d="M5 12.5l4.2 4.2L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
);
export const LockIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" {...S}><rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" /><path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" strokeWidth="1.8" /></svg>
);

// the inkwell + dipping nib — the Companion's writing scene
export const Inkwell = () => (
  <span className="ink-scene" aria-hidden="true">
    <svg viewBox="0 0 44 32" width="44" height="32" fill="none">
      <path className="iw-body" d="M8 18 h16 v6 a3 3 0 0 1 -3 3 H11 a3 3 0 0 1 -3 -3 z" />
      <ellipse className="iw-mouth" cx="16" cy="18" rx="8" ry="2.6" />
      <ellipse className="iw-hi" cx="13" cy="17.4" rx="3" ry="1" />
      <g className="nib-pen">
        <path className="pen-shaft" d="M34 3 L19.5 17.5" />
        <path className="nib-tip" d="M19.5 17.5 l3.4 -1.1 -2.3 -2.3 z" stroke="none" />
      </g>
    </svg>
  </span>
);

// the lit diya — the voice orb on Home
export const Diya = () => (
  <span className="diya" aria-hidden="true">
    <svg className="diya-art" viewBox="0 0 120 112" preserveAspectRatio="xMidYMid meet">
      <ellipse className="diya-pool" cx="60" cy="99" rx="44" ry="6" />
      <path className="lamp-body" d="M13 66 Q26 91 60 92 Q94 91 107 66 Q60 83 13 66 Z" />
      <path className="lamp-shade" d="M13 66 Q60 83 107 66 Q94 78 60 79 Q26 78 13 66 Z" />
      <path className="lamp-rim" d="M13 66 Q60 83 107 66" />
      <path className="wick" d="M60 63 v-6" />
      <g className="flame">
        <path className="flame-outer" d="M60 57 C51 45 52 32 60 20 C68 32 69 45 60 57 Z" />
        <path className="flame-inner" d="M60 54 C54 45 55 36 60 27 C65 36 64 46 60 54 Z" />
        <circle className="flame-core" cx="60" cy="46" r="3.4" />
      </g>
    </svg>
    <span className="flame-halo"></span>
  </span>
);

// the Aangan postage stamp — jharokha arch + diya
export const PostageStamp = () => (
  <svg className="stamp-svg" width="86" height="100" viewBox="0 0 86 100" role="img" aria-label="Aangan postage stamp">
    <rect x="3" y="3" width="80" height="94" rx="2" fill="#f3e7cf" />
    <rect x="3" y="3" width="80" height="94" rx="2" fill="none" stroke="var(--paper)" strokeWidth="5" strokeDasharray="0.5 6.4" strokeLinecap="round" />
    <rect x="9" y="9" width="68" height="82" fill="none" stroke="var(--red)" strokeWidth="1" />
    <path d="M25 60 h36 v-14 a18 18 0 0 0 -36 0 z" fill="var(--olive)" opacity="0.85" />
    <path d="M31 60 h24 v-9 a12 12 0 0 0 -24 0 z" fill="#f3e7cf" />
    <ellipse cx="43" cy="66" rx="9" ry="3.4" fill="var(--red)" />
    <path d="M43 62 q3 -6 0 -10 q-3 4 0 10 z" fill="var(--red)" />
    <text x="43" y="82" textAnchor="middle" fill="var(--red-ink)" fontSize="7" letterSpacing="1.5" fontFamily="var(--mono)">GHAR</text>
    <text x="43" y="20" textAnchor="middle" fill="var(--red-ink)" fontSize="9" fontFamily="var(--deva)">आँगन</text>
  </svg>
);
