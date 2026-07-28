// Voice in/out. Recording via MediaRecorder. Playback prefers Deepgram Aura
// (warm, studio-quality neural TTS from the backend) and falls back to the
// browser's built-in SpeechSynthesis when Aura isn't available.
import { api } from './api';

const MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];

export function pickMimeType() {
  if (typeof MediaRecorder === 'undefined') return null;
  return MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m)) ?? null;
}

export async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = pickMimeType();
  const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  const chunks = [];
  recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
  recorder.start();

  return {
    stop: () =>
      new Promise((resolve) => {
        recorder.onstop = () => {
          stream.getTracks().forEach((t) => t.stop());
          resolve(new Blob(chunks, { type: recorder.mimeType || 'audio/webm' }));
        };
        recorder.stop();
      }),
  };
}

// Warmest, friendliest-sounding voices first, per language. These are the
// system voices people consistently hear as gentle and personable; the
// premium/enhanced/natural variants (when installed) beat the robotic
// defaults by a mile. On macOS, download the higher-quality versions in
// System Settings → Accessibility → Spoken Content → Manage Voices.
const PREFERRED_VOICES = {
  // Ava and Samantha (esp. their Premium/Enhanced builds) are the warmest,
  // most conversational US voices; Zoe/Allison/Serena follow close behind.
  en: [
    'ava', 'samantha', 'zoe', 'allison', 'serena', 'susan', 'nicky',
    'karen', 'moira', 'tessa', 'google us english',
  ],
  // Kiyara and Lekha are the friendliest Hindi voices; Google's is the fallback.
  hi: ['kiyara', 'lekha', 'google हिन्दी', 'google hindi'],
};

function pickVoice(lang) {
  const voices = speechSynthesis.getVoices();
  const inLang = voices.filter((v) => v.lang && v.lang.toLowerCase().startsWith(lang.toLowerCase()));
  if (inLang.length === 0) return null;
  // Prefer a friendly voice in its highest-quality (premium/enhanced) build.
  const wanted = PREFERRED_VOICES[lang.slice(0, 2)] ?? [];
  for (const name of wanted) {
    const nice = inLang.find(
      (v) => v.name.toLowerCase().includes(name) && /premium|enhanced|natural/i.test(v.name),
    );
    if (nice) return nice;
  }
  // Otherwise any premium/enhanced/natural voice beats the default.
  const premium = inLang.find((v) => /premium|enhanced|natural/i.test(v.name));
  if (premium) return premium;
  // Then the friendliest plain voice we can name.
  for (const name of wanted) {
    const match = inLang.find((v) => v.name.toLowerCase().includes(name));
    if (match) return match;
  }
  return inLang[0];
}

// ---- speaking state -------------------------------------------------------
// currentAudio: the Aura <audio> playing right now (so we can stop it).
// speakToken: a generation guard. Every speak() claims a token; if a newer
//   call or a stop happens while it is still fetching, the stale call aborts
//   instead of playing — otherwise a quick double-call (auto-speak + a click)
//   could leave an orphaned, unstoppable audio looping underneath.
// speakingText / listeners: let the UI show a Stop button and reflect exactly
//   which answer is being read.
let currentAudio = null;
let speakToken = 0;
let speakingText = null;
const speakingListeners = new Set();

function setSpeaking(text) {
  speakingText = text;
  speakingListeners.forEach((fn) => { try { fn(text); } catch { /* ignore */ } });
}

// Subscribe to speaking changes — callback gets the text being read, or null
// when it stops. Returns an unsubscribe function.
export function onSpeakingChange(fn) {
  speakingListeners.add(fn);
  return () => speakingListeners.delete(fn);
}

// The text currently being read aloud, or null when silent.
export function speakingNow() {
  return speakingText;
}

function speakBrowser(text, lang = 'en', { warm = false } = {}) {
  if (typeof speechSynthesis === 'undefined') { setSpeaking(null); return; }
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  const voice = pickVoice(utterance.lang);
  if (voice) utterance.voice = voice;
  utterance.volume = 1;
  if (warm) {
    // loving delivery: unhurried, gentle, and warmly bright — a friend
    // reading you a note, not a machine.
    utterance.rate = 0.9;
    utterance.pitch = 1.12;
  } else {
    // still soft and friendly, just a touch more matter-of-fact.
    utterance.rate = 0.94;
    utterance.pitch = 1.06;
  }
  utterance.onend = () => { if (speakingText === text) setSpeaking(null); };
  utterance.onerror = () => { if (speakingText === text) setSpeaking(null); };
  speechSynthesis.speak(utterance);
}

// Cache the synthesised Aura audio by text+language, so playing the same reply
// again is INSTANT — no second round-trip to the TTS service. In-flight
// requests are de-duped so an auto-speak + a click only fetch once.
const audioCache = new Map(); // key -> object URL
const audioInflight = new Map(); // key -> Promise<url|null>
const CACHE_MAX = 24;

function ttsKey(text, lang) {
  return `${lang}::${text}`;
}

function getAudioUrl(text, lang) {
  const key = ttsKey(text, lang);
  if (audioCache.has(key)) return Promise.resolve(audioCache.get(key));
  if (audioInflight.has(key)) return audioInflight.get(key);
  const p = api.postBlob('/speak', { text, language: lang })
    .then((blob) => {
      if (!blob) return null;
      const url = URL.createObjectURL(blob);
      audioCache.set(key, url);
      if (audioCache.size > CACHE_MAX) {
        const oldest = audioCache.keys().next().value;
        URL.revokeObjectURL(audioCache.get(oldest));
        audioCache.delete(oldest);
      }
      return url;
    })
    .finally(() => audioInflight.delete(key));
  audioInflight.set(key, p);
  return p;
}

// Warm the cache ahead of time (e.g. the moment a reply arrives), so pressing
// Read aloud starts speaking with no perceptible delay.
export function prefetchSpeech(text, lang = 'en') {
  if (!text) return;
  getAudioUrl(text, lang).catch(() => {});
}

// Read text aloud. Tries Deepgram Aura (warm neural voice, cached) via the
// backend; on any failure — no key, unsupported language, network, or blocked
// autoplay — it falls back to the browser voice so speech never goes silent.
export async function speak(text, lang = 'en', { warm = false } = {}) {
  stopSpeaking();
  const myToken = ++speakToken;
  setSpeaking(text);
  try {
    const url = await getAudioUrl(text, lang); // instant on a cache hit
    if (myToken !== speakToken) return; // superseded or stopped while fetching
    if (url) {
      const audio = new Audio(url);
      currentAudio = audio;
      const done = () => {
        if (currentAudio === audio) currentAudio = null;
        if (speakingText === text) setSpeaking(null);
      };
      audio.onended = done;
      audio.onerror = done;
      try {
        await audio.play(); // rejects if autoplay is blocked → fall back below
      } catch {
        if (myToken !== speakToken) return;
        currentAudio = null;
        speakBrowser(text, lang, { warm });
      }
      return;
    }
  } catch {
    /* fall through to the browser voice */
  }
  if (myToken !== speakToken) return;
  currentAudio = null;
  speakBrowser(text, lang, { warm });
}

export function stopSpeaking() {
  speakToken += 1; // invalidate any in-flight speak()
  if (currentAudio) {
    currentAudio.pause();
    try { currentAudio.currentTime = 0; } catch { /* ignore */ }
    currentAudio = null;
  }
  if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
  setSpeaking(null);
}
