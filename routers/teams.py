from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models.schemas import APIResponse
from db import get_db
from models.core import Team, User, Role, TeamMember
from utils.jwt import require_admin_user
from sqlalchemy.future import select

router = APIRouter(prefix="/teams", tags=["teams"])

bearer_scheme = HTTPBearer()

# Pydantic Schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    leader_id: Optional[int] = None

class TeamCreate(TeamBase):
    pass

class TeamRead(TeamBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    leader_id: Optional[int] = None

class TeamMemberBase(BaseModel):
    user_id: int
    role: str

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberRead(TeamMemberBase):
    id: int
    joined_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

async def require_admin(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    token = credentials.credentials
    user, error = await require_admin_user(token, db)
    if error:
        return error
    return user

@router.get("", response_model=APIResponse)
async def list_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    teams = result.scalars().all()
    return {
        "success": True,
        "data": [TeamRead.model_validate(team) for team in teams],
        "message": "Teams retrieved successfully."
    }

@router.post("", response_model=APIResponse)
async def create_team(
    team: TeamCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    
    # Filter out fields that don't exist in the model
    team_data = team.model_dump()
    
    # Create a temporary Team object to check attributes 
    temp_team = Team()
    team_data = {k: v for k, v in team_data.items() if hasattr(temp_team, k)}
    
    # Explicitly protect timestamp fields from modification
    protected_fields = {"created_at", "updated_at"}
    team_data = {k: v for k, v in team_data.items() if k not in protected_fields}
    
    db_team = Team(**team_data)
    db.add(db_team)
    await db.commit()
    await db.refresh(db_team)
    return {
        "success": True,
        "data": TeamRead.model_validate(db_team),
        "message": "Team created successfully."
    }

@router.get("/{team_id}", response_model=APIResponse)
async def get_team(team_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        return {
            "success": False,
            "error": {"code": "TEAM_NOT_FOUND", "details": f"No team exists with id {team_id}."},
            "message": "Team not found."
        }
    return {
        "success": True,
        "data": TeamRead.model_validate(team),
        "message": "Team retrieved successfully."
    }

@router.patch("/{team_id}", response_model=APIResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        return {
            "success": False,
            "error": {"code": "TEAM_NOT_FOUND", "details": f"No team exists with id {team_id}."},
            "message": "Team not found."
        }
    
    # Get fields to update and filter out ones that don't exist in the model
    update_data = team_update.model_dump(exclude_unset=True)
    update_data = {k: v for k, v in update_data.items() if hasattr(team, k)}
    
    # Explicitly protect timestamp fields from modification
    protected_fields = {"created_at", "updated_at"}
    update_data = {k: v for k, v in update_data.items() if k not in protected_fields}
    
    # If no valid fields to update
    if not update_data:
        return {
            "success": True,
            "message": "No fields to update."
        }
    
    # Update team
    for key, value in update_data.items():
        setattr(team, key, value)
    
    await db.commit()
    await db.refresh(team)
    return {
        "success": True,
        "data": TeamRead.model_validate(team),
        "message": "Team updated successfully."
    }

@router.delete("/{team_id}", response_model=APIResponse)
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        return {
            "success": False,
            "error": {"code": "TEAM_NOT_FOUND", "details": f"No team exists with id {team_id}."},
            "message": "Team not found."
        }
    await db.delete(team)
    await db.commit()
    return {
        "success": True,
        "message": "Team deleted successfully."
    }

@router.get("/{team_id}/members", response_model=APIResponse)
async def list_team_members(team_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        return {
            "success": False,
            "error": {"code": "TEAM_NOT_FOUND", "details": f"No team exists with id {team_id}."},
            "message": "Team not found."
        }
    result = await db.execute(select(TeamMember).where(TeamMember.team_id == team_id))
    members = result.scalars().all()
    return {
        "success": True,
        "data": [TeamMemberRead.model_validate(member) for member in members],
        "message": "Team members retrieved successfully."
    }

@router.post("/{team_id}/members", response_model=APIResponse)
async def add_team_member(
    team_id: int,
    member: TeamMemberCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    
    # Filter out fields that don't exist in the model
    member_data = member.model_dump()
    
    # Explicitly protect timestamp fields from modification
    protected_fields = {"joined_at"}
    member_data = {k: v for k, v in member_data.items() if k not in protected_fields}
    
    # Check if team exists
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        return {
            "success": False,
            "error": {"code": "TEAM_NOT_FOUND", "details": f"No team exists with id {team_id}."},
            "message": "Team not found."
        }
    # Check if user exists
    result = await db.execute(select(User).where(User.id == member_data["user_id"]))
    user = result.scalars().first()
    if not user:
        return {
            "success": False,
            "error": {"code": "USER_NOT_FOUND", "details": f"No user exists with id {member_data['user_id']}."},
            "message": "User not found."
        }
    # Check if already a member
    result = await db.execute(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == member_data["user_id"]))
    existing = result.scalars().first()
    if existing:
        return {
            "success": False,
            "error": {"code": "ALREADY_MEMBER", "details": f"User {member_data['user_id']} is already a member of team {team_id}."},
            "message": "User is already a member of the team."
        }
    db_member = TeamMember(team_id=team_id, **member_data)
    db.add(db_member)
    await db.commit()
    await db.refresh(db_member)
    return {
        "success": True,
        "data": TeamMemberRead.model_validate(db_member),
        "message": "Member added to team successfully."
    }

@router.delete("/{team_id}/members/{user_id}", response_model=APIResponse)
async def remove_team_member(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    if isinstance(admin, dict) and not admin.get("success", True):
        return admin
    result = await db.execute(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))
    member = result.scalars().first()
    if not member:
        return {
            "success": False,
            "error": {"code": "MEMBER_NOT_FOUND", "details": f"User {user_id} is not a member of team {team_id}."},
            "message": "Member not found in team."
        }
    await db.delete(member)
    await db.commit()
    return {
        "success": True,
        "message": "Member removed from team successfully."
    } 