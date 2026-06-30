from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class GoalCreate(BaseModel):
    title: str
    description: str
    deadline: datetime

class TaskComplete(BaseModel):
    actual_hours: float

class ChatInput(BaseModel):
    message: str
    goal_id: Optional[int] = None

class GoalOut(BaseModel):
    id: int
    title: str
    deadline: datetime
    status: str
    class Config:
        from_attributes = True

class TaskOut(BaseModel):
    id: int
    title: str
    scheduled_date: datetime
    estimated_hours: float
    actual_hours: Optional[float]
    priority: str
    completed: bool
    goal_id: int
    class Config:
        from_attributes = True