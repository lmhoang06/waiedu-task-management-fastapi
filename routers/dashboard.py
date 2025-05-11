from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
async def dashboard_summary():
    return {"message": "Dashboard summary stub"}

@router.get("/recent-activities")
async def dashboard_recent_activities():
    return {"message": "Dashboard recent activities stub"}

@router.get("/stats")
async def dashboard_stats():
    return {"message": "Dashboard stats stub"} 