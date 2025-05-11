from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, BigInteger, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM
from .enums import ProjectStatusEnum, PriorityEnum, TaskStatusEnum
from .core import Base

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    status = Column(ENUM(ProjectStatusEnum, name="project_status_enum"), nullable=False, server_default='pending_approval')
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    manager_id = Column(Integer, ForeignKey('users.id'))
    budget = Column(BigInteger, nullable=False, server_default='0')
    priority = Column(ENUM(PriorityEnum, name="priority_enum"), nullable=False, server_default='medium')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    manager = relationship("User", foreign_keys=[manager_id])
    __table_args__ = (
        CheckConstraint('end_date > start_date', name='valid_project_dates'),
        CheckConstraint('budget >= 0', name='non_negative_budget'),
    )

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    status = Column(ENUM(TaskStatusEnum, name="task_status_enum"), nullable=False, server_default='todo')
    priority = Column(ENUM(PriorityEnum, name="priority_enum"), nullable=False, server_default='medium')
    due_date = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint('due_date > created_at', name='valid_task_due_date'),
    )

class ProjectMember(Base):
    __tablename__ = 'project_members'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(255), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
    )

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("content != ''", name='valid_comment_content'),
    )

class TaskAssignment(Base):
    __tablename__ = 'task_assignments'
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uq_task_user'),
    ) 