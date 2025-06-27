import asyncio
import sys
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers.student import router as student_router
from routers.llm import router as llm_router
import models
from database import engine
from utils.validator import cleanup_sessions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler(sys.stdout)],
)


@asynccontextmanager
async def lifespan():
    async def periodic_cleanup():
        while True:
            await cleanup_sessions()
            await asyncio.sleep(600)  # Run every 10 minutes

    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


models.Base.metadata.create_all(bind=engine)

app.include_router(router=student_router, prefix="/student", tags=["students"])
app.include_router(router=llm_router, prefix="/llm", tags=["llm"])
