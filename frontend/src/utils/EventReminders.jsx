import { speakWithEmotion } from "./voice";

let reminderInterval = null;

export function startEventReminders(getTodayEvents, getMood) {
  // Check immediately on start, then every hour
  checkAndRemind(getTodayEvents, getMood);
  
  reminderInterval = setInterval(() => {
    checkAndRemind(getTodayEvents, getMood);
  }, 60 * 60 * 1000); // every 1 hour

  return () => clearInterval(reminderInterval);
}

function checkAndRemind(getTodayEvents, getMood) {
  const events = getTodayEvents();
  if (!events || events.length === 0) return;

  const now = new Date();

  events.forEach(event => {
    const eventTime = new Date(event.event_date);
    const hoursUntil = (eventTime - now) / ( 10 * 1000); // every 10 seconds — FOR TESTING ONLY, change back to 60*60*1000 before demo

    // Remind if event is happening within the next 1-2 hours and hasn't passed
    if (hoursUntil > 0 && hoursUntil <= 2) {
      const reminderKey = `reminded_${event.id}_${now.getHours()}`;
      if (localStorage.getItem(reminderKey)) return; // already reminded this hour

      const mood = getMood();
      const timeLabel = eventTime.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const message = `Don't forget — ${event.title} is coming up at ${timeLabel}. I remember how that one went, make sure you're ready.`;

      speakWithEmotion(message, mood);
      localStorage.setItem(reminderKey, "true");
    }
  });
}