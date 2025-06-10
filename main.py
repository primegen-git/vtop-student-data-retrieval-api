from fastapi import FastAPI
from routers.student import router as student_router
from routers.llm import router as llm_router

app = FastAPI()

app.include_router(router=student_router, prefix="/student", tags=["students"])
app.include_router(router=llm_router, prefix="/llm", tags=["llm"])
