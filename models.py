from sqlalchemy import Column, String
from database import Base


class Student(Base):
    __tablename__ = "students"

    reg_no = Column(String, primary_key=True)
    profile = Column(String)
    semester = Column(String)
    timetable = Column(String)
    marks = Column(String)
    grade_history = Column(String)
    attendance = Column(String)
