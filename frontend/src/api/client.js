const BASE = "http://localhost:8000";

export const api = {
  sendMessage: (message) =>
    fetch(`${BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    }).then(r => r.json()),

  getGoals: () => fetch(`${BASE}/goals`).then(r => r.json()),

  getTodayTasks: () => fetch(`${BASE}/tasks/today`).then(r => r.json()),

  getGoalTasks: (goalId) => fetch(`${BASE}/goals/${goalId}/tasks`).then(r => r.json()),

  startTimer: (taskId) =>
    fetch(`${BASE}/tasks/${taskId}/timer/start`, { method: "POST" }).then(r => r.json()),

  completeTask: (taskId, actualHours, completionPct) =>
    fetch(`${BASE}/tasks/${taskId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actual_hours: actualHours, completion_pct: completionPct }),
    }).then(r => r.json()),

  getFutureState: () => fetch(`${BASE}/future-state`).then(r => r.json()),

  getMorning: () => fetch(`${BASE}/voice/morning`).then(r => r.json()),

  streamChat: (message, goalId, onToken, onDone) => {
    fetch(`${BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, goal_id: goalId }),
    }).then(async (res) => {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value);
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) onToken(data.token);
              if (data.done) onDone();
            } catch {}
          }
        }
      }
    });
  },
};