const VOICE_PARAMS = {
  proud:      { pitch: 1.1,  rate: 1.0,  volume: 1.0 },
  thrilled:   { pitch: 1.2,  rate: 1.05, volume: 1.0 },
  hopeful:    { pitch: 1.05, rate: 0.95, volume: 0.9 },
  determined: { pitch: 1.0,  rate: 0.98, volume: 1.0 },
  anxious:    { pitch: 0.95, rate: 1.1,  volume: 0.95 },
  stressed:   { pitch: 0.9,  rate: 1.15, volume: 1.0 },
  regretful:  { pitch: 0.85, rate: 0.88, volume: 0.85 },
  neutral:    { pitch: 1.0,  rate: 1.0,  volume: 0.9 },
};

// Pick the best available voice (prefer a natural-sounding one)
let cachedVoice = null;
function getBestVoice() {
  if (cachedVoice) return cachedVoice;
  const voices = window.speechSynthesis.getVoices();
  // Prefer: Google voices > Microsoft > default
  const preferred = ["Google US English", "Microsoft Mark", "Microsoft David", "Alex", "Samantha"];
  for (const name of preferred) {
    const v = voices.find(v => v.name.includes(name));
    if (v) { cachedVoice = v; return v; }
  }
  // Fallback: first English voice
  cachedVoice = voices.find(v => v.lang.startsWith("en")) || voices[0];
  return cachedVoice;
}

export function speakWithEmotion(text, mood = "neutral", onStart, onEnd) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();

  const params = VOICE_PARAMS[mood] || VOICE_PARAMS.neutral;
  const utter = new SpeechSynthesisUtterance(text);
  
  utter.pitch = params.pitch;
  utter.rate = params.rate;
  utter.volume = params.volume;
  
  // Wait for voices to load (Chrome quirk)
  const trySpeak = () => {
    const voice = getBestVoice();
    if (voice) utter.voice = voice;
    utter.onstart = onStart;
    utter.onend = onEnd;
    window.speechSynthesis.speak(utter);
  };

  if (window.speechSynthesis.getVoices().length === 0) {
    window.speechSynthesis.onvoiceschanged = trySpeak;
  } else {
    trySpeak();
  }
}

export function fetchAndSpeak(eventType, context, mood) {
  return fetch("http://localhost:8000/voice/event", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_type: eventType, context, mood }),
  })
    .then(r => r.json())
    .then(data => {
      speakWithEmotion(data.script, data.mood);
      return data;
    });
}

// Morning check-in — call this when dashboard loads
export function morningCheckin(goalId, onData) {
  fetch(`http://localhost:8000/voice/morning/${goalId}`)
    .then(r => r.json())
    .then(data => {
      // Small delay so it feels natural, not instant
      setTimeout(() => {
        speakWithEmotion(data.script, data.mood);
        onData?.(data);
      }, 1500);
    });
}