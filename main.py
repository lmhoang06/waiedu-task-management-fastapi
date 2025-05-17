import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from db import engine, AsyncSessionLocal
from routers.admin_requests import router as admin_requests_router

load_dotenv()

async def lifespan(app):
    # Startup: test DB connection
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: None)
    yield
    # Shutdown: (add cleanup if needed)

app = FastAPI(lifespan=lifespan)

# CORS middleware example (optional, but common for APIs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
from routers import auth, users, roles, teams, projects, tasks, comments, dashboard, reports
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(teams.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)
app.include_router(comments.task_router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(admin_requests_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}