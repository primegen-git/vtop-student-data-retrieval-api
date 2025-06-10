import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from utils.validator import validate_session

logger = logging.getLogger(__name__)

from database import get_db
from models import Student


router = APIRouter()


class ResponseModel(BaseModel):
    success: bool
    data: dict | None


async def fetch_all_records(session_id: str, db: Session, query: str) -> ResponseModel:
    await validate_session(session_id)
    data = None
    try:
        if query == "profile":
            logger.info("fetching profile")
            stmt = select(Student.profile).where(Student.session_id == session_id)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()
        elif query == "semester":
            logger.info("fetching semester")
            stmt = select(Student.semester).where(Student.session_id == session_id)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()
        elif query == "grade_history":
            logger.info("fetching grade_history")
            stmt = select(Student.grade_history).where(Student.session_id == session_id)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()

    except Exception as e:
        logger.error(f"error in getting {query} : {str(e)}", exc_info=True)

    print(data)

    if not data:
        logger.error(f"record does not exist")
        return ResponseModel(success=False, data=None)
    logger.info(f"{query} data successfully fetched from database")
    return ResponseModel(success=True, data=json.loads(data))


async def fetch_records_per_semester(
    session_id: str, sem_id: str | None, db: Session, query: str
) -> ResponseModel:

    await validate_session(session_id)
    response = None
    data = None
    try:
        if query == "marks":
            logger.info("fetching marks from database")
            data = db.execute(
                select(Student.marks).where(Student.session_id == session_id)
            ).scalar_one_or_none()
        elif query == "timetable":
            logger.info("fetching timetable from database")
            data = db.execute(
                select(Student.timetable).where(Student.session_id == session_id)
            ).scalar_one_or_none()
        elif query == "attendance":
            logger.info("fetching attendance from database")
            data = db.execute(
                select(Student.attendance).where(Student.session_id == session_id)
            ).scalar_one_or_none()
        if not data:
            return ResponseModel(success=False, data=None)
        if not sem_id:
            response = json.loads(data)
        else:
            response = json.loads(data)[sem_id]

    except Exception as e:
        logger.error(
            f"error in fetching {query} from database : {str(e)}", exc_info=True
        )

    if not response:
        logger.error("record does not exist")
        return ResponseModel(success=False, data=None)
    logger.info(f"{query} data successfully fetched from database")
    return ResponseModel(success=True, data=response)


@router.get("/semesters", response_model=ResponseModel)
async def get_semesters(session_id: str, db: Session = Depends(get_db)):

    return await fetch_all_records(session_id, db, "semester")


@router.get("/profile", response_model=ResponseModel)
async def get_profile(session_id, db: Session = Depends(get_db)):

    return await fetch_all_records(session_id, db, "profile")


@router.get("/grade_history", response_model=ResponseModel)
async def get_grade_history(session_id, db: Session = Depends(get_db)):

    return await fetch_all_records(session_id, db, "grade_history")


@router.get("/marks", response_model=ResponseModel)
async def get_marks(
    session_id: str, sem_id: Optional[str] = None, db: Session = Depends(get_db)
):
    return await fetch_records_per_semester(session_id, sem_id, db, "marks")


@router.get("/attendance", response_model=ResponseModel)
async def get_attendance(
    session_id: str, sem_id: Optional[str] = None, db: Session = Depends(get_db)
):
    return await fetch_records_per_semester(session_id, sem_id, db, "attendance")


@router.get("/timetable", response_model=ResponseModel)
async def get_timetable(
    session_id: str, sem_id: Optional[str] = None, db: Session = Depends(get_db)
):

    return await fetch_records_per_semester(session_id, sem_id, db, "timetable")
