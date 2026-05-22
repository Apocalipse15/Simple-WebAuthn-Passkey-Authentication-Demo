import logging
import base64
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.config import settings
from app.db import engine, get_session

from app.models.user import Base, User
from app.models.credential import Credential

from app.schemas.user import UserCreate, UserRead
from app.api.auth import router as auth_router

logger = logging.getLogger(__name__)


# -------------------------
# LIFESPAN
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.ENV)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")

    yield

    logger.info("Shutting down application")


# -------------------------
# APP FACTORY
# -------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # -------------------------
    # CORS (IMPORTANT for WebAuthn frontend)
    # -------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------
    # ROUTERS
    # -------------------------
    app.include_router(auth_router)

    # -------------------------
    # BASIC ROUTES
    # -------------------------
    @app.get("/")
    async def root():
        return {"message": "Hello, world"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/health/db")
    async def db_health(db: AsyncSession = Depends(get_session)):
        await db.execute(text("SELECT 1"))
        return {"status": "ok"}

    @app.get("/user")
    async def list_users(db: AsyncSession = Depends(get_session)):
        result = await db.execute(select(User))
        return result.scalars().all()

    # -------------------------
    # CREATE USER (FIXED)
    # -------------------------
    @app.post("/users", response_model=UserRead)
    async def create_user(
        payload: UserCreate,
        db: AsyncSession = Depends(get_session),
    ):
        # check existing user
        result = await db.execute(
            select(User).where(User.username == payload.username)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # base64 decode
        try:
            user_handle_bytes = base64.b64decode(payload.webauthn_user_handle)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 user handle")

        # create user
        user = User(
            username=payload.username,
            display_name=payload.displayname,
            is_verified=payload.is_verified,
            webauthn_user_handle=user_handle_bytes,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    return app