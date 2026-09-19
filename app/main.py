from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .api import auth, order, product


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await db.connect()
    await db.run_migrations(app.state.pool)

    try:
        yield
    finally:
        await db.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(product.router)
app.include_router(order.router)

@app.get("/")
async def root():
    return {"message": "hello world"}
