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
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout),
    ],  # for console output also
    # handlers=[logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")

    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

    async def periodic_cleanup():
        while True:
            try:
                await cleanup_sessions()
                logger.debug("Periodic cleanup completed")
            except Exception as e:
                logger.error(f"Cleanup task failed: {e}")
            await asyncio.sleep(600)  # Run every 10 minutes

    cleanup_task = asyncio.create_task(periodic_cleanup())
    logger.info("Periodic cleanup task started")

    yield

    logger.info("Shutting down application...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("Cleanup task cancelled successfully")
    except Exception as e:
        logger.error(f"Error during cleanup task shutdown: {e}")


app = FastAPI(
    title="VTOP API",
    description="API for VTOP student data management",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router=student_router, prefix="/student", tags=["students"])
app.include_router(router=llm_router, prefix="/llm", tags=["llm"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
