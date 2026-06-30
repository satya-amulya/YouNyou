import { useState, useEffect, useRef } from "react";
import { api } from "../api/client";
import { speakWithEmotion, morningCheckin } from "../utils/voice";

const MOOD_CONFIG = {
  hopeful:     { emoji: "😊", color: "#4ade80", label: "Hopeful" },
  proud:       { emoji: "😎", color: "#a78bfa", label: "Proud" },
  stressed:    { emoji: "😰", color: "#fb923c", label: "Stressed" },
  regretful:   { emoji: "😔", color: "#94a3b8", label: "Regretful" },
  determined:  { emoji: "💪", color: "#60a5fa", label: "Determined" },
  anxious:     { emoji: "😟", color: "#f87171", label: "Anxious" },
  thrilled:    { emoji: "🤩", color: "#fbbf24", label: "Thrilled" },
  neutral:     { emoji: "😐", color: "#94a3b8", label: "Neutral" },
};

export default function FutureYou({ goalId, onVoiceMessage }) {
  const [state, setState] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (!goalId) return;
    api.getFutureState(goalId).then(s => {
      setState(s);
      const lastMorning = localStorage.getItem(`morning_${goalId}`);
      const today = new Date().toDateString();
      if (lastMorning !== today) {
        morningCheckin(goalId, (data) => {
          setMessages([{ role: "assistant", content: data.script }]);
        });
        localStorage.setItem(`morning_${goalId}`, today);
      }
    });
  }, [goalId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const mood = state ? MOOD_CONFIG[state.mood] || MOOD_CONFIG.neutral : MOOD_CONFIG.neutral;
  const speak = (text) => speakWithEmotion(text, state?.mood || "neutral");

  const sendMessage = async () => {
  if (!input.trim() || streaming) return;
  const msg = input.trim();
  setInput("");
  setMessages(prev => [...prev, { role: "user", content: msg }]);
  setStreaming(true);

  // First check if this is a goal/event via the classifier
  const classified = await api.sendMessage(msg);

  if (classified.type === "goal_created" || classified.type === "event_created") {
    setMessages(prev => [...prev, { role: "assistant", content: classified.message }]);
    setStreaming(false);
    speak(classified.message);
    window.dispatchEvent(new Event("refreshDashboard")); // tell Dashboard to refresh
    return;
  }

  // Otherwise, treat as casual chat
  let assistantMsg = "";
  setMessages(prev => [...prev, { role: "assistant", content: "" }]);

  api.streamChat(msg, goalId,
    (token) => {
      assistantMsg += token;
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: assistantMsg };
        return updated;
      });
    },
    () => {
      setStreaming(false);
      speak(assistantMsg);
    }
  );
};

  return (
    <div className="future-you-card">
      <div className="future-header">
        <span className="future-label">FUTURE YOU {mood.emoji}</span>
        <span className="mood-badge" style={{ background: mood.color + "22", color: mood.color }}>
          {mood.label}
        </span>
      </div>
      <div className="avatar-wrapper">
        <div className="mood-ring" style={{ borderColor: mood.color }} />
        <div className="avatar-face">{mood.emoji}</div>
      </div>
      {state?.narrative && (
        <div className="consequence-box" onClick={() => speak(state.narrative)}>
          <p>{state.narrative}</p>
          <span className="speak-hint">🔊 tap to hear</span>
        </div>
      )}
      {state && (
        <div className="future-stats">
          <div className="stat">
            <span className="stat-label">Success chance</span>
            <span className="stat-value" style={{ color: state.success_probability > 0.6 ? "#4ade80" : "#f87171" }}>
              {Math.round(state.success_probability * 100)}%
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">Stress level</span>
            <span className="stat-value" style={{ color: state.stress > 0.6 ? "#f87171" : "#4ade80" }}>
              {state.stress < 0.3 ? "Low" : state.stress < 0.7 ? "Medium" : "High"}
            </span>
          </div>
        </div>
      )}
      <button className="chat-toggle-btn" onClick={() => setChatOpen(o => !o)}>
        {chatOpen ? "Close chat" : "Chat with Future You"}
      </button>
      {chatOpen && (
        <div className="chat-panel">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-placeholder">Ask your future self anything...</div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>
                {m.role === "assistant" && <span className="msg-avatar">{mood.emoji}</span>}
                <div className="msg-bubble">
                  {m.content}
                  {streaming && i === messages.length - 1 && m.role === "assistant" && <span className="cursor">▋</span>}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div className="chat-input-row">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage()}
              placeholder="Ask your future self..."
              className="chat-input"
              disabled={streaming}
            />
            <button onClick={sendMessage} className="send-btn" disabled={streaming}>
              {streaming ? "..." : "→"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}