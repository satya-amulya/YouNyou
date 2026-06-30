from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import json

from database import engine, get_db, Base
from models import Goal, Task, Event, FutureState, ChatMessage, GoalStatus
import agents

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── SCHEMAS ───────────────────────────────────────────────────────
class ChatInput(BaseModel):
    message: str
    goal_id: Optional[int] = None

class TimerStop(BaseModel):
    actual_hours: float
    completion_pct: float  # 0-100
    note: Optional[str] = ""

# ── CHAT — THE MAIN INPUT ─────────────────────────────────────────
@app.post("/chat")
def chat_input(body: ChatInput, db: Session = Depends(get_db)):
    """
    Main entry point. User types anything here.
    Agent classifies and handles automatically.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    classified = agents.classify_input(body.message, today)

    db.add(ChatMessage(user_id=1, role="user", content=body.message))

    if classified["type"] == "goal":
        # Create goal
        deadline_str = classified.get("deadline", (datetime.utcnow() + timedelta(days=3)).isoformat())
        try:
            deadline = datetime.fromisoformat(deadline_str)
        except:
            deadline = datetime.utcnow() + timedelta(days=3)

        goal = Goal(
            title=classified.get("title", body.message[:50]),
            description=classified.get("description", body.message),
            deadline=deadline
        )
        db.add(goal)
        db.flush()

        # Get existing tasks today for distribution
        existing = db.query(Task).filter(
            Task.scheduled_date >= datetime.utcnow().replace(hour=0, minute=0, second=0),
            Task.scheduled_date < datetime.utcnow().replace(hour=23, minute=59, second=59),
            Task.completed == False
        ).all()
        existing_data = [{"title": t.title, "estimated_hours": t.estimated_hours} for t in existing]

        tasks_data = agents.generate_roadmap(goal.title, goal.description, deadline, existing_data)
        for t in tasks_data:
            task = Task(
                goal_id=goal.id,
                title=t["title"],
                description=t.get("description", ""),
                scheduled_date=datetime.strptime(t["scheduled_date"], "%Y-%m-%d"),
                estimated_hours=t["estimated_hours"],
                priority=t["priority"],
            )
            db.add(task)

        db.commit()
        _refresh_future_state(db)

        response_msg = f"Created goal '{goal.title}' with deadline {deadline.strftime('%b %d')}. I've built your roadmap automatically."
        db.add(ChatMessage(user_id=1, role="assistant", content=response_msg))
        db.commit()

        return {
            "type": "goal_created",
            "goal_id": goal.id,
            "message": response_msg,
            "task_count": len(tasks_data)
        }

    elif classified["type"] == "event":
        date_str = classified.get("date", datetime.utcnow().isoformat())
        try:
            event_date = datetime.fromisoformat(date_str)
        except:
            event_date = datetime.utcnow()

        event = Event(
            title=classified.get("title", body.message[:50]),
            description=classified.get("description", ""),
            event_date=event_date,
            duration_hours=classified.get("duration_hours", 1.0)
        )
        db.add(event)
        db.commit()

        response_msg = f"Added '{event.title}' to your schedule on {event_date.strftime('%b %d at %I:%M %p')}."
        db.add(ChatMessage(user_id=1, role="assistant", content=response_msg))
        db.commit()

        return {"type": "event_created", "message": response_msg}

    else:
        response = classified.get("response", "Tell me what you need to accomplish.")
        db.add(ChatMessage(user_id=1, role="assistant", content=response))
        db.commit()
        return {"type": "chat", "message": response}


# ── GOALS ─────────────────────────────────────────────────────────
@app.get("/goals")
def list_goals(db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.status == GoalStatus.active).all()
    result = []
    for g in goals:
        tasks = g.tasks
        completed = sum(1 for t in tasks if t.completed)
        days_left = (g.deadline - datetime.utcnow()).days
        result.append({
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "deadline": g.deadline,
            "days_left": days_left,
            "progress_pct": round(completed / len(tasks) * 100) if tasks else 0,
            "task_count": len(tasks),
            "completed_count": completed,
        })
    return result


# ── TASKS ─────────────────────────────────────────────────────────
@app.get("/tasks/today")
def get_today_tasks(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    tomorrow_end = datetime.combine(today + timedelta(days=1), datetime.max.time())

    today_tasks = db.query(Task).filter(
        Task.scheduled_date >= today_start,
        Task.scheduled_date <= today_end,
    ).order_by(Task.priority.desc(), Task.estimated_hours.desc()).all()

    overdue = db.query(Task).filter(
        Task.scheduled_date < today_start,
        Task.completed == False
    ).all()

    tomorrow_tasks = db.query(Task).filter(
        Task.scheduled_date > today_end,
        Task.scheduled_date <= tomorrow_end,
    ).order_by(Task.priority.desc()).all()

    today_events = db.query(Event).filter(
        Event.event_date >= today_start,
        Event.event_date <= today_end,
    ).all()

    return {
        "today": [_task_dict(t) for t in today_tasks],
        "overdue": [_task_dict(t) for t in overdue],
        "tomorrow": [_task_dict(t) for t in tomorrow_tasks],
        "events": [_event_dict(e) for e in today_events],
    }


@app.get("/goals/{goal_id}/tasks")
def get_goal_tasks(goal_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.goal_id == goal_id).order_by(Task.scheduled_date).all()
    return [_task_dict(t) for t in tasks]


# ── TIMER ─────────────────────────────────────────────────────────
@app.post("/tasks/{task_id}/timer/start")
def start_timer(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404)
    task.timer_started_at = datetime.utcnow()
    db.commit()
    return {"started_at": task.timer_started_at}


@app.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, body: TimerStop, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404)

    task.actual_hours = body.actual_hours
    task.completion_pct = body.completion_pct
    task.completed = body.completion_pct >= 100
    task.completed_at = datetime.utcnow() if task.completed else None
    db.commit()

    goal = db.query(Goal).filter(Goal.id == task.goal_id).first()

    # Get remaining tasks
    remaining = db.query(Task).filter(
        Task.goal_id == task.goal_id,
        Task.completed == False,
        Task.id != task_id
    ).all()
    remaining_data = [{"id": t.id, "title": t.title, "description": t.description or "", 
                       "scheduled_date": str(t.scheduled_date.date()), 
                       "estimated_hours": t.estimated_hours, "priority": t.priority} 
                      for t in remaining]

    # Replan if partial
    voice_message = ""
    if body.completion_pct < 100 and remaining_data:
        replanned = agents.replan_after_partial(
            task.title, task.description or "", body.completion_pct,
            body.actual_hours, task.estimated_hours, remaining_data, goal.deadline
        )
        for rt in replanned:
            if rt.get("id"):
                db_task = db.query(Task).filter(Task.id == rt["id"]).first()
                if db_task:
                    db_task.scheduled_date = datetime.strptime(rt["scheduled_date"], "%Y-%m-%d")
                    db_task.estimated_hours = rt["estimated_hours"]
                    db_task.priority = rt["priority"]
                    if rt.get("description"):
                        db_task.description = rt["description"]
            else:
                # New catch-up task
                new_task = Task(
                    goal_id=task.goal_id,
                    title=rt["title"],
                    description=rt.get("description", ""),
                    scheduled_date=datetime.strptime(rt["scheduled_date"], "%Y-%m-%d"),
                    estimated_hours=rt["estimated_hours"],
                    priority=rt["priority"]
                )
                db.add(new_task)
        db.commit()

    # Generate voice reaction
    state = db.query(FutureState).filter(
        FutureState.goal_id == task.goal_id
    ).order_by(FutureState.generated_at.desc()).first()
    mood = state.mood if state else "neutral"

    if body.completion_pct < 50:
        event_type = "partial_completion"
    elif body.completion_pct < 100:
        event_type = "partial_completion"
    elif body.actual_hours > task.estimated_hours * 1.2:
        event_type = "full_completion_slow"
    else:
        event_type = "full_completion_fast"

    voice_message = agents.generate_voice_reaction(event_type, {
        "task": task.title,
        "pct": body.completion_pct,
        "actual": body.actual_hours,
        "estimated": task.estimated_hours,
    }, mood)

    _refresh_future_state(db)

    return {
        "success": True,
        "voice_message": voice_message,
        "mood": mood,
        "replanned": len(remaining_data) > 0 and body.completion_pct < 100
    }


# ── FUTURE STATE ──────────────────────────────────────────────────
@app.get("/future-state")
def get_future_state(db: Session = Depends(get_db)):
    state = db.query(FutureState).order_by(
        FutureState.generated_at.desc()
    ).first()
    return state


# ── CHAT STREAM ───────────────────────────────────────────────────
@app.post("/chat/stream")
async def chat_stream(body: ChatInput, db: Session = Depends(get_db)):
    history = db.query(ChatMessage).order_by(ChatMessage.created_at).limit(20).all()
    history_data = [{"role": m.role, "content": m.content} for m in history]

    db.add(ChatMessage(user_id=1, role="user", content=body.message))
    db.commit()

    goals = db.query(Goal).filter(Goal.status == GoalStatus.active).all()
    goal_context = []
    for g in goals:
        tasks = g.tasks
        completed = sum(1 for t in tasks if t.completed)
        goal_context.append({
            "title": g.title,
            "deadline": g.deadline.strftime("%Y-%m-%d"),
            "progress": f"{completed}/{len(tasks)} tasks",
            "days_left": (g.deadline - datetime.utcnow()).days
        })

    state = db.query(FutureState).order_by(FutureState.generated_at.desc()).first()
    future_state_data = {
        "mood": state.mood if state else "neutral",
        "success_probability": state.success_probability if state else 0.7,
        "stress": state.stress if state else 0.3
    }

    full_response = []

    async def event_stream():
        async for chunk in agents.stream_future_self_chat(
            body.message, history_data, goal_context, future_state_data
        ):
            full_response.append(chunk)
            yield f"data: {json.dumps({'token': chunk})}\n\n"

        complete = "".join(full_response)
        db.add(ChatMessage(user_id=1, role="assistant", content=complete))
        db.commit()
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── MORNING CHECKIN ───────────────────────────────────────────────
@app.get("/voice/morning")
def morning_checkin(db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.status == GoalStatus.active).all()
    if not goals:
        return {"script": "No active goals. Tell me what you want to accomplish.", "mood": "neutral"}

    g = goals[0]
    tasks = g.tasks
    completed = sum(1 for t in tasks if t.completed)
    pct = (completed / len(tasks) * 100) if tasks else 0
    days_left = (g.deadline - datetime.utcnow()).days

    state = db.query(FutureState).order_by(FutureState.generated_at.desc()).first()
    mood = state.mood if state else "hopeful"

    script = agents.generate_voice_reaction("morning", {
        "goal": g.title, "pct": pct, "days_left": days_left
    }, mood)
    return {"script": script, "mood": mood}


# ── HELPERS ───────────────────────────────────────────────────────
def _task_dict(t):
    return {
        "id": t.id, "goal_id": t.goal_id, "title": t.title,
        "description": t.description, "scheduled_date": str(t.scheduled_date),
        "estimated_hours": t.estimated_hours, "actual_hours": t.actual_hours,
        "completion_pct": t.completion_pct, "priority": t.priority,
        "completed": t.completed, "timer_started_at": str(t.timer_started_at) if t.timer_started_at else None
    }

def _event_dict(e):
    return {
        "id": e.id, "title": e.title, "description": e.description,
        "event_date": str(e.event_date), "duration_hours": e.duration_hours,
        "completed": e.completed, "type": "event"
    }

def _refresh_future_state(db: Session):
    goals = db.query(Goal).filter(Goal.status == GoalStatus.active).all()
    if not goals:
        return

    goals_summary = []
    total_pct = 0
    missed = 0
    days_list = []

    for g in goals:
        tasks = g.tasks
        completed = sum(1 for t in tasks if t.completed)
        pct = (completed / len(tasks) * 100) if tasks else 0
        total_pct += pct
        missed += sum(1 for t in tasks if not t.completed and t.scheduled_date < datetime.utcnow())
        days_list.append((g.deadline - datetime.utcnow()).days)
        goals_summary.append({"title": g.title, "progress": f"{pct:.0f}%", "days_left": (g.deadline - datetime.utcnow()).days})

    avg_pct = total_pct / len(goals)
    avg_days = sum(days_list) / len(days_list) if days_list else 0

    state_data = agents.generate_future_state(goals_summary, avg_pct, missed, avg_days)

    state = FutureState(
        user_id=1,
        goal_id=goals[0].id,
        mood=state_data["mood"],
        confidence=state_data["confidence"],
        stress=state_data["stress"],
        success_probability=state_data["success_probability"],
        narrative=state_data.get("consequence_story", ""),
    )
    db.add(state)
    db.commit()