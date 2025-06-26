import sys
import logging
from fastapi import FastAPI
from routers.student import router as student_router
from routers.llm import router as llm_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler(sys.stdout)],
)

app = FastAPI()

app.include_router(router=student_router, prefix="/student", tags=["students"])
app.include_router(router=llm_router, prefix="/llm", tags=["llm"])
