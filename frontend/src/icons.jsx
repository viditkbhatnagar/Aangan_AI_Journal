// Aangan icon library — hand-inked line icons.
// One weight, rounded ends, drawn like the Chitthi pen. Every icon takes the
// surrounding ink colour (currentColor) and is sized by CSS per context.

const L = {
  viewBox: '0 0 24 24',
  width: 20,
  height: 20,
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
};

/* ---------- primary navigation ---------- */
export const HomeIcon = () => (
  <svg {...L}><path d="M4 11.5 12 4l8 7.5" /><path d="M6 10.4V20h12v-9.6" /><path d="M10 20v-5h4v5" /></svg>
);
export const JournalIcon = () => (
  <svg {...L}><path d="M6 4h9l4 4v12H6z" /><path d="M15 4v4h4" /><path d="M9 12h6M9 15.5h6" /></svg>
);
export const AskIcon = () => (
  <svg {...L}><path d="M5 6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-6l-4 3.5V15H7a2 2 0 0 1-2-2z" /><path d="M12 7.4l.7 1.6 1.8.2-1.3 1.3.3 1.8-1.5-.9-1.5.9.3-1.8-1.3-1.3 1.8-.2z" /></svg>
);
export const AlertsIcon = () => (
  <svg {...L}><path d="M6 10a6 6 0 0 1 12 0c0 4 1.6 5.4 2 5.8H4c.4-.4 2-1.8 2-5.8Z" /><path d="M10 19a2 2 0 0 0 4 0" /></svg>
);
export const ActionsIcon = () => (
  <svg {...L}><path d="M5 8h14l-1 11.5H6z" /><path d="M8.6 8a3.4 3.4 0 0 1 6.8 0" /><path d="M9.5 12v4M14.5 12v4" /></svg>
);
export const MemoryIcon = () => (
  <svg {...L}><rect x="4" y="5" width="16" height="14" rx="1.5" /><path d="M4 15.5l4-3 3 2 3.5-3.5 5.5 4.5" /><circle cx="9" cy="9.2" r="1.3" /></svg>
);
export const MeIcon = () => (
  <svg {...L}><circle cx="12" cy="8.5" r="3.4" /><path d="M5.5 20a6.5 6.5 0 0 1 13 0" /></svg>
);
export const ThoughtsIcon = () => (
  <svg {...L}><path d="M9 18h6M10 20.5h4" /><path d="M12 3.5a6 6 0 0 1 3.6 10.8c-.7.5-1.1 1-1.1 1.7H9.5c0-.7-.4-1.2-1.1-1.7A6 6 0 0 1 12 3.5Z" /></svg>
);

/* ---------- top-bar & controls ---------- */
export const GearIcon = () => (
  <svg {...L} width="16" height="16"><circle cx="12" cy="12" r="3" /><path d="M19.4 13a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-2.9-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 4.6 13H4a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.1-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 11 3.4V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 2.9 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.4 1.9Z" /></svg>
);
export const MicIcon = () => (
  <svg {...L}><rect x="9.5" y="3" width="5" height="11" rx="2.5" /><path d="M6 10.5a6 6 0 0 0 12 0" /><path d="M12 16.5V20" /></svg>
);
export const SpeakerIcon = () => (
  <svg {...L}><path d="M4 9.5h3l4-3.5v12l-4-3.5H4z" /><path d="M15 9a4 4 0 0 1 0 6" /><path d="M17.5 6.5a7.5 7.5 0 0 1 0 11" /></svg>
);
export const TickIcon = () => (
  <svg {...L}><path d="M5 12.5l4.2 4.2L19 7" /></svg>
);
export const LockIcon = () => (
  <svg {...L} width="14" height="14"><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>
);
export const PencilIcon = () => (
  <svg {...L} width="15" height="15"><path d="M5 19l4-1 9.5-9.5-3-3L6 15z" /><path d="M14 6l3 3" /></svg>
);
export const TrashIcon = () => (
  <svg {...L} width="15" height="15"><path d="M5 7h14" /><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" /><path d="M7 7l1 12h8l1-12" /></svg>
);
export const FlagIcon = () => (
  <svg {...L} width="15" height="15"><path d="M6 21V4" /><path d="M6 5h10l-2 3 2 3H6" /></svg>
);
export const NibIcon = () => (
  <svg {...L}><path d="M5 19l3.5-1 8-8-2.5-2.5-8 8z" /><path d="M13.5 7.5l3 3" /><path d="M8.5 18l-.8 1.3" /></svg>
);
export const ChevronIcon = () => (
  <svg {...L} width="14" height="14"><path d="M9 6l6 6-6 6" /></svg>
);

/* ---------- the agent cast ---------- */
export const CompassIcon = () => (
  <svg {...L}><circle cx="12" cy="12" r="8.5" /><path d="M14.8 9.2l-1.6 4-4 1.6 1.6-4z" /></svg>
);
export const LampIcon = () => (
  <svg {...L}><path d="M4 13.5c1.5 3 4.5 4.5 8 4.5s6.5-1.5 8-4.5c-5 2-11 2-16 0Z" /><path d="M12 10.5V8" /><path d="M12 8c-1.4-1.6-1.2-3.4 0-5 1.2 1.6 1.4 3.4 0 5Z" /></svg>
);
export const BookIcon = () => (
  <svg {...L}><path d="M5 5.5A2 2 0 0 1 7 4h11v14H7a2 2 0 0 0-2 2z" /><path d="M18 18a2 2 0 0 0-2-2H5" /><path d="M9 8h6M9 11h5" /></svg>
);
export const FeatherIcon = () => (
  <svg {...L}><path d="M5 19l7.5-7.5a5 5 0 1 1-0.01 0L5 19z" /><path d="M8 16h6" /><path d="M11 8l4 4" /></svg>
);
export const SearchIcon = () => (
  <svg {...L}><circle cx="10.5" cy="10.5" r="5.5" /><path d="M14.5 14.5L19 19" /></svg>
);
export const ShieldIcon = () => (
  <svg {...L}><path d="M12 3.5l7 2.5v5c0 4.4-2.9 8-7 9-4.1-1-7-4.6-7-9V6z" /><path d="M9 12l2 2 4-4.5" /></svg>
);
export const GiftIcon = () => (
  <svg {...L}><rect x="4.5" y="9.5" width="15" height="4" rx="1" /><path d="M6 13.5V20h12v-6.5" /><path d="M12 9.5V20" /><path d="M12 9.5C11 6.5 7 6.5 8 9c.6 1.4 3 .5 4 .5Z" /><path d="M12 9.5c1-3 5-3 4-.5-.6 1.4-3 .5-4 .5Z" /></svg>
);
export const GlobeIcon = () => (
  <svg {...L}><circle cx="12" cy="12" r="8.5" /><path d="M3.5 12h17" /><path d="M12 3.5c2.5 2.4 2.5 14.6 0 17M12 3.5c-2.5 2.4-2.5 14.6 0 17" /></svg>
);
export const SproutIcon = () => (
  <svg {...L}><path d="M12 20v-7" /><path d="M12 13c0-3 2.5-5 6-5 0 3-2.5 5-6 5Z" /><path d="M12 14c0-2.5-2-4.5-5-4.5 0 2.5 2 4.5 5 4.5Z" /></svg>
);
export const RadarIcon = () => (
  <svg {...L}><path d="M12 12a8 8 0 1 0 5.6 2.3" /><path d="M12 12a4 4 0 1 0 2.9 1.2" /><path d="M12 12l7-5" /><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /></svg>
);
export const MirrorIcon = () => (
  <svg {...L}><rect x="6.5" y="3.5" width="11" height="14" rx="5.5" /><path d="M12 17.5V21M9 21h6" /><path d="M10 7.5a2.5 2.5 0 0 0 0 4" /></svg>
);

/* ---------- trace / step glyphs ---------- */
export const NoteIcon = () => (
  <svg {...L}><path d="M6 4h8l4 4v12H6z" /><path d="M14 4v4h4" /><path d="M9 12h6M9 15h4" /></svg>
);
export const StarIcon = () => (
  <svg {...L}><path d="M12 4.5l2.2 4.6 5 .6-3.7 3.4 1 5-4.5-2.5L7.5 18l1-5L4.8 9.7l5-.6z" /></svg>
);
export const HandIcon = () => (
  <svg {...L}><path d="M9 11V5.5a1.4 1.4 0 0 1 2.8 0V11" /><path d="M11.8 10V4.6a1.4 1.4 0 0 1 2.8 0V11" /><path d="M14.6 10.4a1.4 1.4 0 0 1 2.8 0V15a5 5 0 0 1-5 5 5 5 0 0 1-4.3-2.5l-1.7-2.7a1.5 1.5 0 0 1 2.4-1.8l1 1.2" /></svg>
);
export const CartIcon = () => (
  <svg {...L}><path d="M4 5h2l1.5 9.5h9L18 8H7" /><circle cx="9" cy="18.5" r="1.2" /><circle cx="16" cy="18.5" r="1.2" /></svg>
);
export const ChatIcon = () => (
  <svg {...L}><path d="M5 6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-6l-4 3.5V15H7a2 2 0 0 1-2-2z" /><path d="M9 9h6M9 12h4" /></svg>
);
export const PhoneIcon = () => (
  <svg {...L}><path d="M6 3.5h3l1.3 3.4-1.7 1.4a11 11 0 0 0 5 5l1.4-1.7 3.4 1.3v3a1.8 1.8 0 0 1-2 1.8A15.5 15.5 0 0 1 4.2 5.5 1.8 1.8 0 0 1 6 3.5Z" /></svg>
);
export const LinkIcon = () => (
  <svg {...L}><path d="M10 14a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1.5 1.5" /><path d="M14 10a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5l1.5-1.5" /></svg>
);
export const PauseIcon = () => (
  <svg {...L}><rect x="7" y="5" width="3.2" height="14" rx="1" /><rect x="13.8" y="5" width="3.2" height="14" rx="1" /></svg>
);
export const TargetIcon = () => (
  <svg {...L}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4.5" /><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /></svg>
);
export const BulbIcon = () => (
  <svg {...L}><path d="M9 16a5 5 0 1 1 6 0c-.7.5-1 1-1 1.8h-4c0-.8-.3-1.3-1-1.8Z" /><path d="M9.5 20h5M10.5 22h3" /></svg>
);
export const FlaskIcon = () => (
  <svg {...L}><path d="M10 4v5l-4.5 8a1.5 1.5 0 0 0 1.3 2.2h10.4A1.5 1.5 0 0 0 18.5 17L14 9V4" /><path d="M9 4h6" /><path d="M8 14.5h8" /></svg>
);
export const LeafIcon = () => (
  <svg {...L}><path d="M5 19c0-8 6-13 14-13 0 8-5 13-13 13H5Z" /><path d="M6 18c3-4 6-6 10-7" /></svg>
);
export const TeapotIcon = () => (
  <svg {...L}><path d="M5 11h11a4 4 0 0 1-4 6H9a4 4 0 0 1-4-4z" /><path d="M16 12c2 0 3 1 3 2.5" /><path d="M8 11c0-2 1.5-3 3-3s3 1 3 3" /><path d="M10.5 6.2h3" /></svg>
);
export const EnvelopeIcon = () => (
  <svg {...L}><rect x="4" y="6" width="16" height="12" rx="1.5" /><path d="M4.5 7l7.5 6 7.5-6" /></svg>
);

/* ---------- multi-colour decorative marks (kept) ---------- */
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

/* ---------- lookups ---------- */
export const AGENT_ICON = {
  Conductor: CompassIcon,
  Companion: LampIcon,
  Librarian: BookIcon,
  Transcriber: MicIcon,
  Summarizer: FeatherIcon,
  Extractor: SearchIcon,
  'Consent Guardian': ShieldIcon,
  Alerter: AlertsIcon,
  Doer: GiftIcon,
  Interpreter: GlobeIcon,
  Prompter: SproutIcon,
  Radar: RadarIcon,
  'Personal Radar': RadarIcon,
  Reflector: MirrorIcon,
  Speaker: SpeakerIcon,
};

const TRACE_ICON = {
  '📝': NoteIcon, '🧭': CompassIcon, '🔎': SearchIcon, '🔍': SearchIcon,
  '⭐': StarIcon, '🛡️': ShieldIcon, '🛡': ShieldIcon, '✋': HandIcon, '🖐️': HandIcon,
  '✅': TickIcon, '🛒': CartIcon, '💬': ChatIcon, '📞': PhoneIcon, '🔗': LinkIcon,
  '⏸️': PauseIcon, '⏸': PauseIcon, '🌐': GlobeIcon, '🎁': GiftIcon, '🎯': TargetIcon,
  '💡': BulbIcon, '🌱': SproutIcon, '📚': BookIcon, '✍️': FeatherIcon,
  '🎙': MicIcon, '🎙️': MicIcon, '🧠': ThoughtsIcon,
};

// Render a trace-step glyph from the emoji the backend emits, as a line icon.
export function TraceGlyph({ emoji }) {
  const C = TRACE_ICON[emoji];
  return C ? <C /> : <span aria-hidden="true">·</span>;
}
