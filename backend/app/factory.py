import logging
import base64
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Request
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

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.ENV)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")

    yield

    logger.info("Shutting down application")

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

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info("----- REQUEST START -----")

        logger.info("Method: %s", request.method)
        logger.info("URL: %s", request.url)

        headers = dict(request.headers)
        logger.info("Headers: %s", headers)

        logger.info("Cookies: %s", request.cookies)

        body = await request.body()
        if body:
            try:
                logger.info("Body: %s", body.decode("utf-8"))
            except Exception:
                logger.info("Body: <binary data>")

        response = await call_next(request)

        logger.info("Status code: %s", response.status_code)
        logger.info("----- REQUEST END -----")

        return response

    app.include_router(auth_router)

# Auxiliary endpoints

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

    @app.post("/users", response_model=UserRead)
    async def create_user(
        payload: UserCreate,
        db: AsyncSession = Depends(get_session),
    ):
        result = await db.execute(
            select(User).where(User.username == payload.username)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        try:
            user_handle_bytes = base64.b64decode(payload.webauthn_user_handle)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 user handle")

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