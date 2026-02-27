from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, health, users, filters, vacancies


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print(f"🚀 {settings.project_name} v{settings.project_version} запущен")
    yield
    print("👋 Сервис остановлен")


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(filters.router, prefix="/api/v1")
app.include_router(vacancies.router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return {"service": settings.project_name, "docs": "/docs"}
