from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel

# ==========================================
# 1. PROJECT MODELS
# ==========================================

class ProjectBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = None

class Project(ProjectBase, table=True):
    """Database table schema for Projects."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tasks: List["Task"] = Relationship(back_populates="project")

class ProjectCreate(ProjectBase):
    """Data required from client to create a Project."""
    pass

class ProjectRead(ProjectBase):
    """Data returned to client when reading a Project."""
    id: int


# ==========================================
# 2. TASK MODELS
# ==========================================

class TaskBase(SQLModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    project_id: int = Field(foreign_key="project.id")

class Task(TaskBase, table=True):
    """Database table schema for Tasks."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project: Optional[Project] = Relationship(back_populates="tasks")

class TaskCreate(TaskBase):
    """Data required from client to create a Task."""
    pass

class TaskRead(TaskBase):
    """Data returned to client when reading a Task."""
    id: int

class TaskUpdate(SQLModel):
    """Fields that can be optionally updated for a Task."""
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None