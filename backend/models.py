from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class GoalStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    failed = "failed"

class ItemType(str, enum.Enum):
    goal = "goal"
    event = "event"

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=1)
    title = Column(String(255))
    description = Column(Text)
    deadline = Column(DateTime)
    status = Column(Enum(GoalStatus), default=GoalStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    tasks = relationship("Task", back_populates="goal", cascade="all, delete")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    title = Column(String(255))
    description = Column(Text, nullable=True)
    scheduled_date = Column(DateTime)
    estimated_hours = Column(Float)
    actual_hours = Column(Float, nullable=True)
    completion_pct = Column(Float, default=0)  # 0-100
    priority = Column(String(20), default="medium")
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    timer_started_at = Column(DateTime, nullable=True)
    goal = relationship("Goal", back_populates="tasks")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=1)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    event_date = Column(DateTime)
    duration_hours = Column(Float, default=1.0)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FutureState(Base):
    __tablename__ = "future_states"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=1)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    mood = Column(String(50))
    confidence = Column(Float)
    stress = Column(Float)
    success_probability = Column(Float)
    narrative = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=1)
    role = Column(String(10))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)