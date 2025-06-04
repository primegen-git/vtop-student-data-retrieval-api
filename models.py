from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    registration_number = Column(String, unique=True)
    name = Column(String)
    branch = Column(String)
    enrollements = relationship("Enrollement", back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    name = Column(String)
    code = Column(String)
    enrollements = relationship("Enrollement", back_populates="course")


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    code = Column(String, primary_key=True)
    name = Column(String)
    enrollements = relationship("Enrollement", back_populates="semester")


class Enrollement(Base):
    __tablename__ = "enrollements"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    semester_id = Column(Integer, ForeignKey("semesters.id"))

    student = relationship("Students", back_populates="enrollements")
    course = relationship("Courses", back_populates="enrollements")
    semester = relationship("Semester", back_populates="enrollements")
    marks = relationship("Mark", back_populates="enrollements")
    timetable = relationship("TimeTable", back_populates="enrollements")


class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    enrollments_id = Column(Integer, ForeignKey("enrollments.id"))
    enrollments = relationship("Enrollement", back_populates="marks")


class TimeTable(Base):
    __tablename__ = "timettables"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    enrollments_id = Column(Integer, ForeignKey("enrollments.id"))
    enrollments = relationship("Enrollement", back_populates="timetable")
