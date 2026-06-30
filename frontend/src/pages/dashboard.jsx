import { useState, useEffect, useRef } from "react";
import { api } from "../api/client";
import FutureYou from "../components/FutureYou";
import TodayPlan from "../components/TodayPlan";
import Journey from "../components/Journey";
import { speakWithEmotion } from "../utils/voice";
import { startEventReminders } from "../utils/eventReminders";

export default function Dashboard() {
  const [goals, setGoals] = useState([]);
  const [activeGoalId, setActiveGoalId] = useState(null);
  const [voiceMsg, setVoiceMsg] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const chatEndRef = useRef(null);
  const [todayEvents, setTodayEvents] = useState([]);
 const [currentMood, setCurrentMood] = useState("neutral");

 useEffect(() => {
  api.getTodayTasks().then(data => setTodayEvents(data.events || []));
 }, [refresh]);

 useEffect(() => {
  api.getFutureState().then(s => {
    if (s?.mood) setCurrentMood(s.mood);
  });
 }, [refresh]);

 useEffect(() => {
  const stop = startEventReminders(
    () => todayEvents,
    () => currentMood
  );
  return stop;
 }, [todayEvents, currentMood]);

  useEffect(() => {
    api.getGoals().then(g => {
      setGoals(g);
      if (g.length > 0) setActiveGoalId(g[0].id);
    });
  }, [refresh]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  useEffect(() => {
  const handler = () => setRefresh(r => r + 1);
  window.addEventListener("refreshDashboard", handler);
  return () => window.removeEventListener("refreshDashboard", handler);
  }, []);

  const sendMessage = async () => {
    if (!chatInput.trim() || sending) return;
    const msg = chatInput.trim();
    setChatInput("");
    setSending(true);

    setChatMessages(prev => [...prev, { role: "user", content: msg }]);

    const result = await api.sendMessage(msg);

    if (result.type === "goal_created" || result.type === "event_created") {
      setRefresh(r => r + 1);
      setChatMessages(prev => [...prev, { role: "assistant", content: result.message, type: result.type }]);
    } else {
      setChatMessages(prev => [...prev, { role: "assistant", content: result.message }]);
    }

    setSending(false);
  };

  const handleVoice = (msg) => {
    setVoiceMsg(msg);
    setTimeout(() => setVoiceMsg(""), 10000);
  };

  return (
    <div className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">✦</div>
          <div>
            <div className="brand-name">YouNYou</div>
            <div className="brand-sub">You and your future you</div>
          </div>
        </div>
        <nav className="nav-tabs">
          {goals.map(g => (
            <button
              key={g.id}
              className={`nav-tab ${activeGoalId === g.id ? "active" : ""}`}
              onClick={() => setActiveGoalId(g.id)}
            >
              {g.title}
              <span className="tab-progress">{g.progress_pct}%</span>
              <span className="tab-deadline">{g.days_left}d left</span>
            </button>
          ))}
        </nav>
      </header>

      {voiceMsg && (
        <div className="voice-banner" onClick={() => setVoiceMsg("")}>
          <span>🔊</span> <em>{voiceMsg}</em> <span className="dismiss">✕</span>
        </div>
      )}

      <div className="main-grid">
        <TodayPlan
          onTaskComplete={() => setRefresh(r => r + 1)}
          onVoiceMessage={handleVoice}
          onRefresh={refresh}
        />
        <FutureYou goalId={activeGoalId} onVoiceMessage={handleVoice} />
        <Journey goalId={activeGoalId} />
      </div>

      {/* Main chat input at bottom */}
      <div className="bottom-chat">
        <div className="bottom-chat-messages">
          {chatMessages.length === 0 && (
            <p className="bottom-placeholder">
              Tell me what you need to get done — I'll build your roadmap, schedule events, and plan everything.
            </p>
          )}
          {chatMessages.map((m, i) => (
            <div key={i} className={`bottom-msg ${m.role}`}>
              {m.role === "assistant" && <span className="bot-dot">✦</span>}
              <span className="bottom-bubble">{m.content}</span>
              {m.type === "goal_created" && <span className="created-badge">Goal created</span>}
              {m.type === "event_created" && <span className="created-badge event">Event added</span>}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <div className="bottom-input-row">
          <input
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && sendMessage()}
            placeholder="I need to finish 20 maths problems by tomorrow... / Meeting at 7pm today..."
            className="bottom-input"
            disabled={sending}
          />
          <button onClick={sendMessage} disabled={sending} className="bottom-send">
            {sending ? "..." : "→"}
          </button>
        </div>
      </div>
    </div>
  );
}