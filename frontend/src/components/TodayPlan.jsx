import { useState, useEffect } from "react";
import { api } from "../api/client";
import TaskTimer from "./TaskTimer";
import { speakWithEmotion } from "../utils/voice";

const PRIORITY_COLOR = { high: "#E2574C", medium: "#E8A33D", low: "#1F9E78" };

export default function TodayPlan({ onTaskComplete, onVoiceMessage, onRefresh }) {
  const [data, setData] = useState({ today: [], overdue: [], tomorrow: [], events: [] });

  const refresh = () => api.getTodayTasks().then(setData);

  useEffect(() => { refresh(); }, [onRefresh]);

  const handleComplete = (result, actualHours, pct, task) => {
    if (result.voice_message) {
      speakWithEmotion(result.voice_message, result.mood || "neutral");
      onVoiceMessage?.(result.voice_message);
    }
    refresh();
    onTaskComplete?.();
  };

  const TaskRow = ({ task, overdue = false }) => (
    <div className={`task-row ${task.completed ? "done" : ""} ${overdue ? "overdue" : ""}`}>
      <div className="priority-bar" style={{ background: PRIORITY_COLOR[task.priority] || "#94a3b8" }} />
      <div className="task-info">
        {overdue && <span className="overdue-badge">OVERDUE</span>}
        <span className={`task-title ${task.completed ? "strikethrough" : ""}`}>{task.title}</span>
        {task.description && <span className="task-desc">{task.description}</span>}
        <span className="task-est">{task.estimated_hours}h estimated</span>
      </div>
      <TaskTimer task={task} onComplete={handleComplete} />
    </div>
  );

  const EventRow = ({ event }) => (
    <div className="task-row event-row">
      <div className="priority-bar" style={{ background: "#5B4FE8" }} />
      <div className="task-info">
        <span className="task-title">📅 {event.title}</span>
        {event.description && <span className="task-desc">{event.description}</span>}
        <span className="task-est">
          {new Date(event.event_date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · {event.duration_hours}h
        </span>
      </div>
    </div>
  );

  const totalToday = data.today.length + data.events.length;
  const doneToday = data.today.filter(t => t.completed).length;

  return (
    <div className="today-card">
      <div className="card-header">
        <span className="card-label">Present you</span>
        <span className="task-count">{doneToday}/{totalToday} done</span>
      </div>

      {data.overdue.length > 0 && (
        <div className="section-block">
          <div className="section-label overdue-label">⚠ Overdue</div>
          {data.overdue.map(t => <TaskRow key={t.id} task={t} overdue />)}
        </div>
      )}

      <div className="section-block">
        <div className="section-label">Today</div>
        {data.today.map(t => <TaskRow key={t.id} task={t} />)}
        {data.events.map(e => <EventRow key={`e-${e.id}`} event={e} />)}
        {data.today.length === 0 && data.events.length === 0 && (
          <p className="empty-state">Tell me what you need to get done today.</p>
        )}
      </div>

      {data.tomorrow.length > 0 && (
        <div className="section-block tomorrow-block">
          <div className="section-label">Tomorrow's preview</div>
          {data.tomorrow.map(t => (
            <div key={t.id} className="tomorrow-row">
              <span className="j-dot" style={{ background: PRIORITY_COLOR[t.priority] || "#94a3b8" }} />
              <span className="tomorrow-title">{t.title}</span>
              <span className="j-hours">{t.estimated_hours}h</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}