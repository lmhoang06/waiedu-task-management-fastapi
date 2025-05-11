from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/project-stats")
async def project_stats():
    return {"message": "Project stats stub"}

@router.get("/user-stats")
async def user_stats():
    return {"message": "User stats stub"}

@router.get("/team-stats")
async def team_stats():
    return {"message": "Team stats stub"}

@router.get("/export")
async def export_report():
    return {"message": "Export report stub"} 