import { useState, useEffect } from "react";
import { api } from "../api/client";

export default function Journey({ goalId }) {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    if (!goalId) return;
    api.getGoalTasks(goalId).then(setTasks);
  }, [goalId]);

  const grouped = tasks.reduce((acc, t) => {
    const date = new Date(t.scheduled_date).toLocaleDateString("en-US", { month: "short", day: "numeric" });
    if (!acc[date]) acc[date] = [];
    acc[date].push(t);
    return acc;
  }, {});

  return (
    <div className="journey-card">
      <div className="card-header">
        <span className="card-label">YOUR JOURNEY</span>
        <span className="task-count">{tasks.filter(t => t.completed).length}/{tasks.length}</span>
      </div>
      <div className="journey-list">
        {Object.entries(grouped).map(([date, dayTasks]) => (
          <div key={date} className="day-group">
            <span className="day-label">{date}</span>
            {dayTasks.map(t => (
              <div key={t.id} className={`journey-task ${t.completed ? "done" : ""}`}>
                <span className="j-dot" style={{ background: t.completed ? "#4ade80" : "#334155" }} />
                <span className="j-title">{t.title}</span>
                <span className="j-hours">{t.estimated_hours}h</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}