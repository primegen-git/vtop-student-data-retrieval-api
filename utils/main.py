from fastapi import HTTPException
import time
from httpx import AsyncClient
from utils.scrape import profile_scrape
from sqlalchemy.orm import Session
import models


class VtopScraper:
    def __init__(
        self, client: AsyncClient, session_id: str, csrf_token, reg_no: str, db: Session
    ):
        self.client = client
        self.session_id = session_id
        self.csrf_token = csrf_token
        self.reg_no = reg_no
        self.db = db

    async def scrape_all(self):
        await self.scrape_profile()
        await self.scrape_semester()
        await self.scrape_course()
        await self.scrape_marks()
        await self.scrape_timetable()
        await self.scrape_grader_history()

    async def scrape_profile(self):
        PROFILE_URL = (
            "https://vtopcc.vit.ac.in/vtop/studentsRecord/StudentProfileAllView"
        )
        try:

            nocache_value = int(time.time() * 1000)

            profile_payload = {
                "verifyMenu": "true",
                "authorizedID": self.reg_no,
                "_csrf": self.csrf_token,
                "nocache": str(nocache_value),
            }

            profile_response = await self.client.post(
                url=PROFILE_URL,
                data=profile_payload,
            )
            profile_response.raise_for_status()

            profile_data = profile_scrape.extract_profile(profile_response.text)

            if profile_data:

                try:
                    student_model = models.Student(
                        session_id=self.session_id,
                        registration_number=profile_data["registration_number"],
                        name=profile_data["name"],
                        branch_name=profile_data["branch_name"],
                    )

                    self.db.add(student_model)

                    self.db.commit()

                    self.db.refresh(student_model)

                    print("successfully created the Student column")
                    print(student_model)

                except Exception as e:
                    self.db.rollback()
                    raise HTTPException(500, f"Database error {str(e)}")
            else:
                raise ValueError("does not able extract student profile data")

        except Exception as e:
            raise HTTPException(500, f"error  in scraping {str(e)}")

    async def scrape_course(self):
        pass

    async def scrape_semester(self):
        pass

    async def scrape_timetable(self):
        pass

    async def scrape_marks(self):
        pass

    async def scrape_grader_history(self):
        pass
