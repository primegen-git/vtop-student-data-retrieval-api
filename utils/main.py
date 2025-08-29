import json
from email.utils import formatdate
from fastapi import HTTPException
import time
from httpx import AsyncClient
from sqlalchemy import Column
from utils.scrape import (
    profile_scrape,
    semester_scrape,
    timetable_scrape,
    marks_scrape,
    grade_history_scrape,
    attendance_scrape,
    gpa_per_semester,
)
from sqlalchemy.orm import Session
import models
import logging
from .validator import delete_session, delete_csrf_token
from utils.semester_pre_process import semester_pre_process


class VtopScraper:
    def __init__(self, client: AsyncClient, reg_no: str, csrf_token, db: Session):
        self.client = client
        self.csrf_token = csrf_token
        self.reg_no = reg_no
        self.profile = None
        self.semester = None
        self.timetable = None
        self.marks = None
        self.grade_history = None
        self.credits_info = None
        self.cgpa_details = None
        self.grades_count = None
        self.attendance = None
        self.db = db
        self.name = None

        self.logger = logging.getLogger(__name__)

    async def save_to_database(self):
        try:
            self.logger.info("checking if the user exist in the database")

            # Check if student with reg_no exists
            existing_student = (
                self.db.query(models.Student)
                .filter(models.Student.reg_no == self.reg_no)
                .first()
            )

            if existing_student:
                self.logger.info("student exists, updating the record")
                existing_student.profile = Column(json.dumps(self.profile))
                existing_student.semester = Column(json.dumps(self.semester))
                existing_student.timetable = Column(json.dumps(self.timetable))
                existing_student.marks = Column(json.dumps(self.marks))
                existing_student.grade_history = Column(json.dumps(self.grade_history))
                existing_student.attendance = Column(json.dumps(self.attendance))
                existing_student.credits_info = Column(json.dumps(self.credits_info))
                existing_student.grades_count = Column(json.dumps(self.grades_count))
                existing_student.cgpa_details = Column(json.dumps(self.cgpa_details))

                self.db.commit()
                self.db.refresh(existing_student)
                self.logger.info("student record updated successfully")
            else:
                self.logger.info("student does not exist, creating new record")
                student_model = models.Student(
                    reg_no=self.reg_no,
                    profile=json.dumps(self.profile),
                    semester=json.dumps(self.semester),
                    timetable=json.dumps(self.timetable),
                    marks=json.dumps(self.marks),
                    grade_history=json.dumps(self.grade_history),
                    attendance=json.dumps(self.attendance),
                    credits_info=json.dumps(self.credits_info),
                    grades_count=json.dumps(self.grades_count),
                    cgpa_details=json.dumps(self.cgpa_details),
                )

                self.db.add(student_model)
                self.db.commit()
                self.db.refresh(student_model)

                self.logger.info("student model is created successfully")

        except Exception as e:
            self.logger.error(f"Error occurred: {e}")
            self.db.rollback()
            raise

    async def scrape_all(self):
        self.profile = await self.scrape_profile()

        if self.profile:
            self.name = self.profile.get("name")

        self.semester = await self.scrape_semester()

        self.timetable = await self.scrape_timetable()

        self.cgpa_details = await self.scrape_gpa_per_semester()

        self.marks = await self.scrape_marks()

        (
            self.grade_history,
            self.credits_info,
            cgpa,
            self.grades_count,
        ) = await self.scrape_grader_history_and_cgpa_and_grade_count()

        if self.cgpa_details:
            if cgpa:
                self.cgpa_details["cgpa"] = cgpa
            else:
                self.cgpa_details["cpga"] = 0

        self.attendance = await self.scrape_attendance()

        await self.save_to_database()

        await self.clean_up()

        return self.name

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
            return None

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
            return None

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
            return semester_pre_process(semester_data, reg_no=self.reg_no)

        except Exception as e:
            self.logger.error(f"error in scraping semester : {str(e)}")
            return None

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

                    try:
                        timetable_response.raise_for_status()
                        self.logger.info("request completed successfully")
                    except Exception as e:
                        self.logger.error(f"error in response {e}", exc_info=True)

                    timetable_data = timetable_scrape.extract_timetable_info(
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
            return None

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

                    # if not marks_data:
                    #     self.logger.error("error in scraping marks", exc_info=True)
                    #     raise HTTPException(500, detail="error in scraping marks")

                    marks_dict[sem_id] = marks_data

                    self.logger.info(
                        f"marks scraping completed for semester : {self.semester[sem_id]}"
                    )

                self.logger.info("marks scraping completed")
                return marks_dict

        except Exception as e:
            self.logger.error(f"Error in scraping {str(e)}", exc_info=True)
            return None

    async def scrape_gpa_per_semester(self):

        gpa_dict = {}

        try:
            self.logger.info("started scraping gpa per semester")

            GRADE_URL = "https://vtopcc.vit.ac.in/vtop/examinations/examGradeView/doStudentGradeView"

            if self.semester:
                for sem_id in self.semester.keys():
                    gpa_payload = {
                        "authorizedID": self.reg_no,
                        "semesterSubId": sem_id,
                        "_csrf": self.csrf_token,
                    }

                    self.logger.info(
                        f"request send to url : {GRADE_URL} with payload : {gpa_payload}"
                    )

                    gpa_response = await self.client.post(
                        url=GRADE_URL, data=gpa_payload
                    )

                    try:
                        gpa_response.raise_for_status()
                        self.logger.info("request completed successfully")
                    except Exception as e:
                        self.logger.error(f"error in response {e}", exc_info=True)

                    gpa = gpa_per_semester.extract_gpa(gpa_response.text)

                    if not gpa:
                        self.logger.error(
                            "error in parsing gpa(either gpa has not been uploaded or something else)",
                            exc_info=True,
                        )
                        gpa = 0

                    gpa_dict[sem_id] = gpa

                    self.logger.info("scrape gpa for semester")

                self.logger.info("complete gpa parsing")
                return gpa_dict

        except Exception as e:
            self.logger.error(
                f"error in scraping grades per semester {str(e)}", exc_info=True
            )
            if self.semester:
                for sem_id in self.semester.keys():
                    if sem_id in gpa_dict:
                        continue
                    else:
                        gpa_dict[sem_id] = 0
                return gpa_dict

    async def scrape_grader_history_and_cgpa_and_grade_count(self):
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

            grade_history_data, credits_info, cgpa, grades_count = (
                grade_history_scrape.extract_grade_history(grade_history_response.text)
            )

            if not grade_history_data:
                self.logger.error("No grade history data retrived", exc_info=True)
                raise HTTPException(500, detail="error in scraping grade history data")

            self.logger.info("successfully get grade history data")

            self.logger.info("successfully cgpa details")

            return (grade_history_data, credits_info, cgpa, grades_count)

        except Exception as e:
            self.logger.error(
                f"error in scraping grade history {str(e)}", exc_info=True
            )
            return (None, None, None, None)

    async def clean_up(self):
        try:
            await delete_session(self.reg_no)
            await delete_csrf_token(self.reg_no)
        except Exception as e:
            self.logger.error(f"error in clean up {e}")
