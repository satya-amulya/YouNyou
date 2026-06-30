import re
import json
from datetime import datetime, timedelta



def _call(prompt: str, system: str = "") -> str:
    """
    Central mock response function. Routes based on prompt content.
    Replace this function's body with real Gemini calls when quota allows.
    """
    full_prompt = f"{system}\n\n{prompt}".lower()

    # Future Self CHAT responses (conversational, short)
    if "future self" in full_prompt and "chat response" in full_prompt:
     if "did we" in full_prompt or "will i" in full_prompt or "succeed" in full_prompt:
        return "That depends entirely on what you do this week. Right now I'd say it's close — keep pushing."
     elif "scared" in full_prompt or "worried" in full_prompt or "anxious" in full_prompt:
        return "I felt that too. But every time you sat down and just started, it got easier. Trust that."
     elif "task" in full_prompt or "new" in full_prompt:
        return "Noted. I'll factor that into the plan — just make sure you actually start it today, not tomorrow."
     elif "hey" in full_prompt or "hi" in full_prompt:
        return "Hey. What do you want to know about where we end up?"
    else:
        return "I remember asking myself the same thing. Keep showing up — that's what got me here."

    # Voice reactions (emotional, first-person, NOT json)
    if "you are the future self" in full_prompt or "you are the future_self" in full_prompt:
        if "partial" in full_prompt:
            return "I remember this exact moment. You stopped halfway through, and I felt it — the weight of that unfinished work followed me for days. Every problem you skip today becomes two problems tomorrow, and I'm living proof of what happens when you let that pile up. Go finish it now."
        elif "fast" in full_prompt:
            return "I remember that day — we were ahead of schedule and it felt incredible. That extra time you saved today gave me room to breathe later. Keep this pace."
        elif "slow" in full_prompt:
            return "Because of that delay, I had to scramble later than I wanted to. You finished it, which matters, but watch the pace tomorrow."
        elif "missed" in full_prompt:
            return "Because you skipped that today, I walked into the deadline unprepared and I could feel it. Tomorrow has to be different — there's no more room to lose."
        elif "morning" in full_prompt:
            return "Today decides a lot. Stay focused on what's in front of you and the rest will follow."
        else:
            return "Every action you take right now directly shapes who I become. Keep going."

    # Future state generation — returns structured JSON (used internally only)
    if "success_probability" in full_prompt and "consequence_story" in full_prompt:
        return json.dumps({
            "mood": "stressed",
            "confidence": 0.6,
            "stress": 0.65,
            "success_probability": 0.65,
            "short_message": "You're behind. Every hour matters now.",
            "consequence_story": "Because you only finished part of the work today, tomorrow is going to be brutal. I remember sitting there at 2am trying to catch up, and it wasn't pretty."
        })

    # Replan — returns JSON array
    if "replan" in full_prompt or "remaining tasks to replan" in full_prompt:
        return json.dumps([
            {"id": None, "title": "Catch-up session", "description": "Finish the remaining work from today's incomplete task", "scheduled_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"), "estimated_hours": 1.5, "priority": "high"},
            {"id": None, "title": "Continue planned work", "description": "Proceed with the next scheduled portion", "scheduled_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"), "estimated_hours": 1.0, "priority": "medium"}
        ])

    # Roadmap generation — returns JSON array
    if "roadmap" in full_prompt or "break this goal" in full_prompt:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        return json.dumps([
            {"title": "Part 1 — foundation", "description": "Complete the first section thoroughly", "scheduled_date": today, "estimated_hours": 1.5, "priority": "high"},
            {"title": "Part 2 — core work", "description": "Main bulk of the task", "scheduled_date": today, "estimated_hours": 1.5, "priority": "high"},
            {"title": "Part 3 — finish and review", "description": "Complete remaining work and verify", "scheduled_date": tomorrow, "estimated_hours": 1.0, "priority": "medium"}
        ])

    # Default fallback
    return "I understand. Keep going — every action you take right now directly shapes who I am."


# ============================================================
# CLASSIFY USER INPUT — pure Python, no AI needed
# ============================================================
def classify_input(message: str, current_date: str) -> dict:
    msg_lower = message.lower()

    event_words = ["meeting", "call", "appointment", "interview", "class at", "exam at", "session"]
    is_event = any(w in msg_lower for w in event_words)

    goal_words = ["solve", "complete", "finish", "build", "learn", "homework", "project", "problems", "write", "study", "prepare"]
    is_goal = any(w in msg_lower for w in goal_words)

    if is_event:
        time_match = re.search(r'(\d{1,2})\s?(am|pm)', msg_lower)
        hour = 12
        if time_match:
            hour = int(time_match.group(1))
            if time_match.group(2) == "pm" and hour != 12:
                hour += 12

        today = datetime.utcnow()
        event_date = today.replace(hour=hour, minute=0, second=0, microsecond=0)
        if "tomorrow" in msg_lower:
            event_date += timedelta(days=1)

        return {
            "type": "event",
            "title": message[:60].strip().capitalize(),
            "description": message,
            "date": event_date.isoformat(),
            "duration_hours": 1.0
        }

    elif is_goal:
        today = datetime.utcnow()
        deadline = today + timedelta(days=3)

        if "today" in msg_lower:
            deadline = today.replace(hour=23, minute=0)
        elif "tomorrow" in msg_lower:
            deadline = (today + timedelta(days=1)).replace(hour=23, minute=0)
        elif "week" in msg_lower:
            deadline = today + timedelta(days=7)
        else:
            day_match = re.search(r'(\d+)\s?day', msg_lower)
            if day_match:
                deadline = today + timedelta(days=int(day_match.group(1)))

        return {
            "type": "goal",
            "title": message[:60].strip().capitalize(),
            "description": message,
            "deadline": deadline.isoformat()
        }

    else:
        return {
            "type": "chat",
            "response": "Tell me what you need to accomplish — a task with a deadline, or an event to schedule."
        }


# ============================================================
# ROADMAP AGENT
# ============================================================
def generate_roadmap(goal_title: str, goal_desc: str, deadline: datetime, existing_tasks: list = []) -> list:
    days_left = (deadline - datetime.utcnow()).days
    existing_info = ""
    if existing_tasks:
        existing_info = f"\nExisting tasks already scheduled today: {json.dumps(existing_tasks)}\nDistribute around these."

    prompt = f"""
You are a productivity planner. Break this goal into specific daily tasks with descriptions.

Goal: {goal_title}
Details: {goal_desc}
Deadline: {deadline.strftime('%Y-%m-%d')} ({days_left} days from now)
Today: {datetime.utcnow().strftime('%Y-%m-%d')}
{existing_info}

Return ONLY valid JSON array:
[{{
  "title": "specific task name",
  "description": "exactly what to do in this task, be specific",
  "scheduled_date": "YYYY-MM-DD",
  "estimated_hours": 1.5,
  "priority": "high|medium|low"
}}]
"""
    raw = _call(prompt).replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except:
        return [
            {"title": f"{goal_title} - Part 1", "description": "Begin working on the goal", "scheduled_date": datetime.utcnow().strftime("%Y-%m-%d"), "estimated_hours": 1.5, "priority": "high"},
            {"title": f"{goal_title} - Part 2", "description": "Continue and complete", "scheduled_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"), "estimated_hours": 1.5, "priority": "medium"},
        ]


# ============================================================
# PARTIAL COMPLETION REPLAN
# ============================================================
def replan_after_partial(
    task_title: str,
    task_description: str,
    completion_pct: float,
    actual_hours: float,
    estimated_hours: float,
    remaining_tasks: list,
    deadline: datetime
) -> list:
    days_left = (deadline - datetime.utcnow()).days
    remaining_work_pct = 100 - completion_pct

    prompt = f"""
A task was partially completed. Replan remaining tasks accordingly.

TASK: "{task_title}"
Description: {task_description}
Completion: {completion_pct:.0f}% done ({remaining_work_pct:.0f}% remaining)
Time spent: {actual_hours:.1f}h (estimated was {estimated_hours:.1f}h)
Days left until deadline: {days_left}
Today: {datetime.utcnow().strftime('%Y-%m-%d')}

REMAINING TASKS TO REPLAN:
{json.dumps(remaining_tasks, default=str)}

Return ONLY valid JSON array:
[{{"id": original_task_id_or_null_for_new, "title": "task name", "description": "specific what to do", "scheduled_date": "YYYY-MM-DD", "estimated_hours": 1.5, "priority": "high|medium|low"}}]
"""
    raw = _call(prompt).replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except:
        return remaining_tasks


# ============================================================
# FUTURE SELF EMOTION
# ============================================================
def generate_future_state(
    goals_summary: list,
    total_completion_pct: float,
    missed_count: int,
    days_pressure: int
) -> dict:
    prompt = f"""
Generate the emotional state of a person's FUTURE SELF based on their current progress.

CURRENT SITUATION:
Goals: {json.dumps(goals_summary)}
Overall completion: {total_completion_pct:.0f}%
Tasks missed/partial today: {missed_count}
Average days until deadlines: {days_pressure}

Return ONLY valid JSON:
{{
  "mood": "hopeful|proud|stressed|regretful|determined|anxious|thrilled",
  "confidence": 0.75,
  "stress": 0.3,
  "success_probability": 0.82,
  "short_message": "2 sentences from future self to present self",
  "consequence_story": "3-4 sentences — vivid, emotional, specific story"
}}
"""
    raw = _call(prompt).replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except:
        return {
            "mood": "hopeful", "confidence": 0.7, "stress": 0.4,
            "success_probability": 0.72,
            "short_message": "You're doing okay. Keep the momentum.",
            "consequence_story": "Because you stayed consistent today, things came together better than expected."
        }


# ============================================================
# VOICE REACTION — always returns plain text, never JSON
# ============================================================
def generate_voice_reaction(event_type: str, context: dict, mood: str) -> str:
    reactions = {
        "partial_completion": f"""
You are the FUTURE SELF of this person, speaking with a {mood} emotional tone.
They just completed only {context.get('pct', 0):.0f}% of "{context.get('task', 'the task')}" today.
They spent {context.get('actual', 0):.1f} hours but only finished part of it.
PARTIAL completion reaction needed.
""",
        "full_completion_fast": f"""
You are the FUTURE SELF. They finished "{context.get('task', '')}" in {context.get('actual', 0):.1f}h — FAST, faster than estimate.
""",
        "full_completion_slow": f"""
You are the FUTURE SELF. They finished "{context.get('task', '')}" but took longer than estimated. SLOW completion.
""",
        "task_missed": f"""
You are the FUTURE SELF. The task "{context.get('task', '')}" was MISSED today entirely.
""",
        "morning": f"""
You are the FUTURE SELF giving a MORNING check-in.
Goal: "{context.get('goal', '')}", {context.get('days_left', 0)} days left, {context.get('pct', 0):.0f}% done.
"""
    }

    prompt = reactions.get(event_type, "Say something encouraging as the future self.")
    return _call(prompt).strip()


# ============================================================
# FUTURE SELF CHAT — streaming generator, plain text only
# ============================================================
async def stream_future_self_chat(message: str, history: list, goal_context: dict, future_state: dict):
    prompt = f"FUTURE SELF chat response to: {message}"
    response_text = _call(prompt)
    yield response_text