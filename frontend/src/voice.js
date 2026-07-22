// Browser voice in/out: MediaRecorder capture and SpeechSynthesis playback.

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

// Nicest-sounding voices first, per language. Premium/enhanced system voices
// beat the robotic defaults by a mile when they're installed.
const PREFERRED_VOICES = {
  en: ['samantha', 'ava', 'allison', 'susan', 'karen', 'serena', 'google us english'],
  hi: ['lekha', 'kiyara', 'google हिन्दी', 'google hindi'],
};

function pickVoice(lang) {
  const voices = speechSynthesis.getVoices();
  const inLang = voices.filter((v) => v.lang && v.lang.toLowerCase().startsWith(lang.toLowerCase()));
  if (inLang.length === 0) return null;
  const premium = inLang.find((v) => /premium|enhanced|natural/i.test(v.name));
  if (premium) return premium;
  const wanted = PREFERRED_VOICES[lang.slice(0, 2)] ?? [];
  for (const name of wanted) {
    const match = inLang.find((v) => v.name.toLowerCase().includes(name));
    if (match) return match;
  }
  return inLang[0];
}

export function speak(text, lang = 'en', { warm = false } = {}) {
  if (typeof speechSynthesis === 'undefined') return;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  const voice = pickVoice(utterance.lang);
  if (voice) utterance.voice = voice;
  if (warm) {
    // loving delivery: unhurried, a touch brighter
    utterance.rate = 0.88;
    utterance.pitch = 1.06;
  } else {
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
  }
  speechSynthesis.speak(utterance);
}

export function stopSpeaking() {
  if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
}
