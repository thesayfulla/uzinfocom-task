from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings
from . import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await db.connect()
    await db.run_migrations(app.state.pool)

    try:
        yield
    finally:
        await db.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    settings = Settings()
    return {"message": "hello world"}
