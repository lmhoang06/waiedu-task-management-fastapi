from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, BigInteger, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM
from .enums import UserStatusEnum, ForgotPasswordRequestEnum

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(63), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255))
    full_name = Column(String(255))
    role_id = Column(Integer, ForeignKey('roles.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    status = Column(ENUM(UserStatusEnum, name="user_status_enum"), nullable=False, server_default='pending_approval')
    last_login = Column(DateTime(timezone=True))
    avatar = Column(String(255))
    role = relationship('Role', back_populates='users')

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    permissions = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    users = relationship('User', back_populates='role')

class UserToken(Base):
    __tablename__ = 'user_tokens'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        CheckConstraint('expires_at > created_at', name='expires_after_creation'),
    )

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    leader_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class TeamMember(Base):
    __tablename__ = 'team_members'
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(255), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
    )

class ForgotPasswordRequest(Base):
    __tablename__ = 'forgot_password_requests'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    new_password = Column(String(255), nullable=False)
    status = Column(ENUM(ForgotPasswordRequestEnum, name="forgot_password_request_enum"), nullable=False, server_default='pending_approval')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user = relationship('User') 