import { useState, useEffect, useRef } from "react";
import { api } from "../api/client";

export default function TaskTimer({ task, onComplete }) {
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [showPopup, setShowPopup] = useState(false);
  const [completionPct, setCompletionPct] = useState(100);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [running]);

  const fmt = (s) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return h > 0
      ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`
      : `${m}:${String(sec).padStart(2, "0")}`;
  };

  const handleStart = async () => {
    await api.startTimer(task.id);
    setRunning(true);
    setElapsed(0);
  };

  const handleStop = () => {
    setRunning(false);
    setShowPopup(true);
  };

  const handleConfirm = async () => {
    const actualHours = parseFloat((elapsed / 3600).toFixed(2)) || 0.1;
    const result = await api.completeTask(task.id, actualHours, completionPct);
    setShowPopup(false);
    onComplete?.(result, actualHours, completionPct, task);
  };

  if (task.completed) {
    return (
      <span className="task-done-badge">
        ✓ {task.actual_hours ? `${task.actual_hours.toFixed(1)}h` : "done"}
      </span>
    );
  }

  if (showPopup) {
    return (
      <div className="completion-popup">
        <div className="popup-inner">
          <p className="popup-title">How much did you complete?</p>
          <div className="pct-row">
            <input
              type="range"
              min="0"
              max="100"
              step="10"
              value={completionPct}
              onChange={e => setCompletionPct(Number(e.target.value))}
              className="pct-slider"
            />
            <span className="pct-label">{completionPct}%</span>
          </div>
          <p className="popup-time">Time spent: {fmt(elapsed)}</p>
          <div className="popup-btns">
            <button onClick={handleConfirm} className="confirm-btn">Done</button>
            <button onClick={() => { setShowPopup(false); setRunning(true); }} className="cancel-btn">Keep going</button>
          </div>
        </div>
      </div>
    );
  }

  if (running) {
    return (
      <div className="timer-running">
        <span className="timer-live">{fmt(elapsed)}</span>
        <button className="stop-btn" onClick={handleStop}>Stop</button>
      </div>
    );
  }

  return (
    <button className="start-btn" onClick={handleStart}>▶ Start</button>
  );
}