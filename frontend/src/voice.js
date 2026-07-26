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

// The Aura audio currently playing, so we can stop it on demand.
let currentAudio = null;

function speakBrowser(text, lang = 'en', { warm = false } = {}) {
  if (typeof speechSynthesis === 'undefined') return;
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
  speechSynthesis.speak(utterance);
}

// Read text aloud. Tries Deepgram Aura (warm neural voice) via the backend;
// on any failure — no key, unsupported language, network, or blocked autoplay —
// it falls back to the browser voice so speech never simply goes silent.
export async function speak(text, lang = 'en', { warm = false } = {}) {
  stopSpeaking();
  try {
    const blob = await api.postBlob('/speak', { text, language: lang });
    if (blob) {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudio = audio;
      const cleanup = () => {
        URL.revokeObjectURL(url);
        if (currentAudio === audio) currentAudio = null;
      };
      audio.onended = cleanup;
      audio.onerror = cleanup;
      await audio.play(); // rejects if autoplay is blocked → fall back below
      return;
    }
  } catch {
    /* fall through to the browser voice */
  }
  currentAudio = null;
  speakBrowser(text, lang, { warm });
}

export function stopSpeaking() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
}
