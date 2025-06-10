import json
import aiofiles
from email.utils import formatdate
from fastapi import HTTPException
import time
from httpx import AsyncClient
from utils.scrape import (
    profile_scrape,
    semester_scrape,
    timetable_scrape,
    marks_scrape,
    grade_history_scrape,
    attendance_scrape,
)
from sqlalchemy.orm import Session
import models
import logging


class VtopScraper:
    def __init__(
        self, client: AsyncClient, session_id: str, csrf_token, reg_no: str, db: Session
    ):
        self.client = client
        self.session_id = session_id
        self.csrf_token = csrf_token
        self.reg_no = reg_no
        self.profile = None
        self.semester = None
        self.timetable = None
        self.marks = None
        self.grade_history = None
        self.attendance = None
        self.db = db

        self.logger = logging.getLogger(__name__)

    async def save_to_database(self):
        try:
            self.logger.info("saving to database started")
            student_model = models.Student(
                session_id=self.session_id,
                profile=json.dumps(self.profile),
                semester=json.dumps(self.semester),
                timetable=json.dumps(self.timetable),
                marks=json.dumps(self.marks),
                grade_history=json.dumps(self.grade_history),
                attendance=json.dumps(self.attendance),
            )

            self.db.add(student_model)
            self.db.commit()
            self.db.refresh(student_model)

            self.logger.info("student model is created successfully")
            print("successfully saved to database")

        except Exception as e:
            self.db.rollback()
            self.logger.error(f"error in database saving : {str(e)}", exc_info=True)

    async def scrape_all(self):
        self.profile = await self.scrape_profile()
        print("profile scraping completed")
        self.semester = await self.scrape_semester()
        print("semester scraping completed")
        self.timetable = await self.scrape_timetable()
        print("timetable scraping completed")
        self.marks = await self.scrape_marks()
        print("marks scraping completed")
        self.grade_history = await self.scrape_grader_history()
        print("grade_history scraping completed")
        self.attendance = await self.scrape_attendance()
        print("attendance scraping completed")

        await self.save_to_database()

        # async with aiofiles.open("test.txt", "w", encoding="utf-8") as file:
        #
        #     await file.write(json.dumps(self.profile))
        #     await file.write("\n")
        #
        #     await file.write(json.dumps(self.semester))
        #     await file.write("\n")
        #
        #     await file.write(json.dumps(self.timetable))
        #     await file.write("\n")
        #
        #     await file.write(json.dumps(self.marks))
        #     await file.write("\n")
        #
        #     await file.write(json.dumps(self.grade_history))
        #     await file.write("\n")
        #
        #     await file.write(json.dumps(self.attendance))
        #     await file.write("\n")
        #
        self.logger.info("scraping completed")

    async def scrape_profile(self):
        try:
            self.logger.info("started scraping profile")
            PROFILE_URL = (
                "https://vtopcc.vit.ac.in/vtop/studentsRecord/StudentProfileAllView"
            )

            nocache_value = int(time.time() * 1000)

            profile_payload = {
                "verifyMenu": "true",
                "authorizedID": self.reg_no,
                "_csrf": self.csrf_token,
                "nocache": str(nocache_value),
            }

            self.logger.info(
                f"request send to {PROFILE_URL} with payload : {profile_payload}"
            )

            profile_response = await self.client.post(
                url=PROFILE_URL,
                data=profile_payload,
            )
            try:
                profile_response.raise_for_status()
                self.logger.info("request completed successfully")
            except Exception as e:
                self.logger.error(f"error in response {e}", exc_info=True)

            self.logger.info("request completed successfully")

            profile_data = profile_scrape.extract_profile(profile_response.text)

            if not profile_data:
                self.logger.error("No profile data retrived", exc_info=True)
                raise HTTPException(500, detail="error in scraping profile data")

            self.logger.info("successfully get profile data")
            return profile_data

        except Exception as e:
            self.logger.error(f"error in scraping profile : {str(e)}", exc_info=True)

    async def scrape_attendance(self):
        try:
            self.logger.info("started scraping attendance")

            ATTENDANCE_URL = (
                "https://vtopcc.vit.ac.in/vtop/processViewStudentAttendance"
            )

            attendance_dict = {}

            if self.semester:
                for sem_id in self.semester.keys():
                    x_value = formatdate(timeval=None, localtime=False, usegmt=True)
                    attendance_payload = {
                        "authorizedID": self.reg_no,
                        "semesterSubId": sem_id,
                        "_csrf": self.csrf_token,
                        "x": x_value,
                    }

                    self.logger.info(
                        f"request send to url : {ATTENDANCE_URL} with payload : {attendance_payload}"
                    )

                    attendance_response = await self.client.post(
                        url=ATTENDANCE_URL, data=attendance_payload
                    )

                    try:
                        attendance_response.raise_for_status()
                        self.logger.info("request completed successfully")
                    except Exception as e:
                        self.logger.error(f"error in response {e}", exc_info=True)

                    attendance_data = attendance_scrape.extract_attendance(
                        attendance_response.text
                    )

                    if not attendance_data:
                        self.logger.error("error in parsing attendance", exc_info=True)
                        raise HTTPException(
                            500, detail="error in parsing attendance data"
                        )
                    attendance_dict[sem_id] = attendance_data

                    self.logger.info(
                        f"scrape attendance for semester : {self.semester[sem_id]}"
                    )

                self.logger.info("complete attendance parsing")
                return attendance_dict

        except Exception as e:
            self.logger.error("error in scraping attendance", exc_info=True)

    async def scrape_semester(self):
        try:
            self.logger.info("started scraping semester")
            SEMESTER_URL = (
                "https://vtopcc.vit.ac.in/vtop/academics/common/StudentTimeTableChn"
            )

            nocache_value = int(time.time() * 1000)

            semester_payload = {
                "verifyMenu": "true",
                "authorizedID": self.reg_no,
                "_csrf": self.csrf_token,
                "nocache": str(nocache_value),
            }

            self.logger.info(
                f"request send to url : {SEMESTER_URL}, with paylaod : {semester_payload}"
            )

            semester_response = await self.client.post(
                url=SEMESTER_URL, data=semester_payload
            )

            try:
                semester_response.raise_for_status()
                self.logger.info("request completed successfully")
            except Exception as e:
                self.logger.error(f"error in response {e}", exc_info=True)

            self.logger.info("request to url : {PROFILE_URL}, successfull")

            semester_data = semester_scrape.extract_semester(semester_response.text)

            if not semester_data:
                self.logger.error(
                    "semester data does not found, method extract_semeter return None",
                    exc_info=True,
                )
                raise HTTPException(500, detail="semester extraction failed")

            self.logger.info("successfully extracted semester data")
            return semester_data

        except Exception as e:
            self.logger.error(f"error in scraping semester : {str(e)}")

    async def scrape_timetable(self):
        try:
            self.logger.info("started parsing timetable")

            TIMETABLE_URL = "https://vtopcc.vit.ac.in/vtop/processViewTimeTable"

            timetable_dict = {}

            if self.semester:
                for sem_id in self.semester.keys():
                    x_value = formatdate(timeval=None, localtime=False, usegmt=True)
                    timetable_payload = {
                        "authorizedID": self.reg_no,
                        "semesterSubId": sem_id,
                        "_csrf": self.csrf_token,
                        "x": x_value,
                    }

                    self.logger.info(
                        f"request send to url : {timetable_payload} with payload : {timetable_payload}"
                    )

                    timetable_response = await self.client.post(
                        url=TIMETABLE_URL, data=timetable_payload
                    )

                    print(timetable_response)

                    try:
                        timetable_response.raise_for_status()
                        self.logger.info("request completed successfully")
                    except Exception as e:
                        self.logger.error(f"error in response {e}", exc_info=True)

                    timetable_data = timetable_scrape.extract_timetable(
                        timetable_response.text
                    )

                    if not timetable_data:
                        self.logger.error("error in parsing timetable", exc_info=True)
                        raise HTTPException(
                            500, detail="error in parsing timetable data"
                        )
                    timetable_dict[sem_id] = timetable_data

                    self.logger.info(
                        f"scrape timetable for semester : {self.semester[sem_id]}"
                    )

                self.logger.info("complete timetable parsing")
                return timetable_dict

        except Exception as e:
            self.logger.error(f"error in scraping timetable {str(e)}", exc_info=True)

    async def scrape_marks(self):
        try:
            self.logger.info("started scraping marks")
            MARKS_URL = "https://vtopcc.vit.ac.in/vtop/examinations/doStudentMarkView"

            marks_dict = {}

            if self.semester:
                for sem_id in self.semester.keys():
                    marks_payload = {
                        "authorizedID": self.reg_no,
                        "_csrf": self.csrf_token,
                        "semesterSubId": sem_id,
                    }

                    self.logger.info(
                        f"request to url : {MARKS_URL} with payload : {marks_payload}"
                    )

                    marks_response = await self.client.post(
                        url=MARKS_URL, data=marks_payload
                    )

                    try:
                        marks_response.raise_for_status()
                        self.logger.info("request to marks_url successfull")
                    except Exception as e:
                        self.logger.error(
                            f"error in marks_url response : {str(e)}", exc_info=True
                        )

                    marks_data = marks_scrape.extract_marks(marks_response.text)

                    if not marks_data:
                        self.logger.error("error in scraping marks", exc_info=True)
                        raise HTTPException(500, detail="error in scraping marks")

                    marks_dict[sem_id] = marks_data

                    self.logger.info(
                        f"marks scraping completed for semester : {self.semester[sem_id]}"
                    )

                self.logger.info("marks scraping completed")
                return marks_dict

        except Exception as e:
            self.logger.error(f"Error in scraping {str(e)}", exc_info=True)

    async def scrape_grader_history(self):
        try:
            self.logger.info("started scraping grade_history")
            GRADE_HISTORY_URL = "https://vtopcc.vit.ac.in/vtop/examinations/examGradeView/StudentGradeHistory"

            nocache_value = int(time.time() * 1000)

            grade_history_payload = {
                "verifyMenu": "true",
                "authorizedID": self.reg_no,
                "_csrf": self.csrf_token,
                "nocache": str(nocache_value),
            }

            self.logger.info(
                f"request send to {GRADE_HISTORY_URL} with payload : {grade_history_payload}"
            )

            grade_history_response = await self.client.post(
                url=GRADE_HISTORY_URL,
                data=grade_history_payload,
            )
            try:
                grade_history_response.raise_for_status()
                self.logger.info("request completed successfully")
            except Exception as e:
                self.logger.error(f"error in response {e}", exc_info=True)

            self.logger.info("request completed successfully")

            grade_history_data = grade_history_scrape.extract_grade_history(
                grade_history_response.text
            )

            if not grade_history_data:
                self.logger.error("No profile data retrived", exc_info=True)
                raise HTTPException(500, detail="error in scraping profile data")

            self.logger.info("successfully get profile data")
            return grade_history_data

        except Exception as e:
            self.logger.error(
                f"error in scraping grade history {str(e)}", exc_info=True
            )
