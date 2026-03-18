from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db import engine, get_settings
from routers import users, logs, chat, scheduler, reports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🌱 {settings.APP_NAME} starting up...")
    yield
    # Shutdown
    await engine.dispose()
    print(f"👋 {settings.APP_NAME} shut down.")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI-powered health coaching for 50+",
    lifespan=lifespan,
)

# CORS — allow local dev + production frontend
_origins = ["http://localhost:3000"]
if settings.FRONTEND_URL:
    _origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(logs.router)
app.include_router(scheduler.router)
app.include_router(reports.router)


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "env": settings.APP_ENV}