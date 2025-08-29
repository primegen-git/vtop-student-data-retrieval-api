import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models import Student
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class ResponseModel(BaseModel):
    success: bool
    data: dict | None | float


async def fetch_all_records(reg_no: str, db: Session, query: str) -> ResponseModel:
    """
    return the record based on the query provided
    query : [ "profile", "semester", "grade_history"]
    """
    data = None
    try:
        if query == "profile":
            logger.info("fetching profile")
            stmt = select(Student.profile).where(Student.reg_no == reg_no)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()

        elif query == "semester":
            logger.info("fetching semester")
            stmt = select(Student.semester).where(Student.reg_no == reg_no)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()

        elif query == "grade_history":
            logger.info("fetching grade_history")
            stmt = select(Student.grade_history).where(Student.reg_no == reg_no)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()

        elif query == "credits_info":
            logger.info("fetching credits_info")
            stmt = select(Student.credits_info).where(Student.reg_no == reg_no)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()

        elif query == "grades_count":
            logger.info("fetching grades_count")
            stmt = select(Student.grades_count).where(Student.reg_no == reg_no)
            result = db.execute(stmt)
            data = result.scalar_one_or_none()

    except Exception as e:
        logger.error(f"error in getting {query} : {str(e)}", exc_info=True)

    if not data:
        logger.error(f"record does not exist")
        return ResponseModel(success=False, data=None)
    logger.info(f"{query} data successfully fetched from database")
    return ResponseModel(success=True, data=json.loads(data))


async def fetch_records_per_semester(
    reg_no: str, sem_id: str | None, db: Session, query: str
) -> ResponseModel:
    """
    return the student record semester wise if not provided return records for all semester
    """
    response = None
    data = None
    try:
        if query == "marks":
            logger.info("fetching marks from database")
            data = db.execute(
                select(Student.marks).where(Student.reg_no == reg_no)
            ).scalar_one_or_none()

        elif query == "cgpa_details":
            logger.info("fetching cgpa_details from database")
            data = db.execute(
                select(Student.cgpa_details).where(Student.reg_no == reg_no)
            ).scalar_one_or_none()

        elif query == "timetable":
            logger.info("fetching timetable from database")
            data = db.execute(
                select(Student.timetable).where(Student.reg_no == reg_no)
            ).scalar_one_or_none()
        elif query == "attendance":
            logger.info("fetching attendance from database")
            data = db.execute(
                select(Student.attendance).where(Student.reg_no == reg_no)
            ).scalar_one_or_none()
        if not data:
            logger.error("record does not exist")
            return ResponseModel(success=False, data=None)
        if not sem_id:
            response = json.loads(data)
        else:
            try:
                response = json.loads(data)[sem_id]
            except KeyError:
                logger.warning(f"Semester ID {sem_id} not found in data")
                return ResponseModel(success=False, data=None)
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
async def get_semesters(reg_no: str, db: Session = Depends(get_db)):
    try:
        return await fetch_all_records(reg_no, db, "semester")
    except Exception as e:
        logger.error(f"Error in get_semesters: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)  # changed: added error return


@router.get("/profile", response_model=ResponseModel)
async def get_profile(reg_no, db: Session = Depends(get_db)):
    try:
        return await fetch_all_records(reg_no, db, "profile")
    except Exception as e:
        logger.error(f"Error in get_profile: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)  # changed: added error return


@router.get("/grade_history", response_model=ResponseModel)
async def get_grade_history(reg_no, db: Session = Depends(get_db)):
    try:
        return await fetch_all_records(reg_no, db, "grade_history")
    except Exception as e:
        logger.error(f"Error in get_grade_history: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)  # changed: added error return


@router.get("/grades_count", response_model=ResponseModel)
async def get_grades_count(reg_no, db: Session = Depends(get_db)):
    try:
        return await fetch_all_records(reg_no, db, "grades_count")
    except Exception as e:
        logger.error(f"Error in get_grades_count: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)


@router.get("/credits_info", response_model=ResponseModel)
async def get_credits_info(reg_no, db: Session = Depends(get_db)):
    try:
        return await fetch_all_records(reg_no, db, "credits_info")
    except Exception as e:
        logger.error(f"Error in get_credits_info: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)


@router.get("/cgpa_details", response_model=ResponseModel)
async def get_cgpa_details(
    reg_no: str, sem_id: Optional[str] = None, db: Session = Depends(get_db)
):
    try:
        return await fetch_records_per_semester(reg_no, sem_id, db, "cgpa_details")
    except Exception as e:
        logger.error(f"Error in cgpa_details: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)  # changed: added error return


@router.get("/attendance", response_model=ResponseModel)
async def get_attendance(
    reg_no: str, sem_id: Optional[str] = None, db: Session = Depends(get_db)
):
    try:
        return await fetch_records_per_semester(reg_no, sem_id, db, "attendance")
    except Exception as e:
        logger.error(f"Error in get_attendance: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)  # changed: added error return


@router.get("/timetable", response_model=ResponseModel)
async def get_timetable(
    reg_no: str, sem_id: Optional[str] = None, db: Session = Depends(get_db)
):
    try:
        return await fetch_records_per_semester(reg_no, sem_id, db, "timetable")
    except Exception as e:
        logger.error(f"Error in get_timetable: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)


@router.get("/courses", response_model=ResponseModel)
async def get_courses(reg_no: str, db: Session = Depends(get_db)):
    """
    Returns a JSON of all course keys and their names for the given reg_no.
    Use marks like process, but from that resp just puck id n name
    """
    try:
        stmt = select(Student.timetable).where(Student.reg_no == reg_no)
        result = db.execute(stmt)
        timetable_data = result.scalar_one_or_none()
        if not timetable_data:
            logger.error("timetable does not exist.")
            return ResponseModel(
                success=False,
                data={"msg": "timetable does not exist. load data again."},
            )

        data = json.loads(timetable_data)

        course_mappings = {}

        for _, sem_data in data.items():
            for _, timetable in sem_data.items():
                for period in timetable:
                    c_code = period.get("course_code", "")
                    c_name = period.get("course_name", "")

                    if not c_code or not c_name:
                        continue

                    else:
                        if c_code not in course_mappings:
                            course_mappings[c_code] = c_name

        logger.info("Courses data successfully fetched from database")
        return ResponseModel(success=True, data=course_mappings)

    except Exception as e:
        logger.error(f"Error in get_courses: {e}", exc_info=True)
        return ResponseModel(success=False, data=None)


# NOTE: changes to timetable because marks for the current semester does not exist in the begining.

# @router.get("/courses", response_model=ResponseModel)
# async def get_courses(reg_no: str, db: Session = Depends(get_db)):
#     """
#     Returns a JSON of all course keys and their names for the given reg_no.
#     Use marks like process, but from that resp just puck id n name
#     """
#     try:
#         stmt = select(Student.marks).where(Student.reg_no == reg_no)
#         result = db.execute(stmt)
#         marks_data = result.scalar_one_or_none()
#         if not marks_data:
#             logger.error("Marks data does not exist")
#             return ResponseModel(success=False, data=None)
#
#         marks = json.loads(marks_data)
#         course_mappings = {}
#         for courses in marks.values():
#             for course_code, course_info in courses.items():
#                 course_mappings[course_code] = course_info.get(
#                     "course_name", "Unknown Course"
#                 )
#
#         if not course_mappings:
#             logger.warning("No courses found")
#             return ResponseModel(success=False, data=None)
#         logger.info("Courses data successfully fetched from database")
#         return ResponseModel(success=True, data=course_mappings)
#
#     except Exception as e:
#         logger.error(f"Error in get_courses: {e}", exc_info=True)
#         return ResponseModel(success=False, data=None)
