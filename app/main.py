from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings
from . import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await db.connect()

    try:
        yield
    finally:
        await db.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    settings = Settings()
    return {"values": settings.__dict__}
