from fastapi import FastAPI, HTTPException
from mongoengine import connect, disconnect, Document, StringField, IntField, ListField, ReferenceField
from pydantic import BaseModel
import json
from bson import json_util

app = FastAPI()

@app.on_event("startup")
def startup_db_client():
    connect("fast-api-database", host="mongo", port=27017)

@app.on_event("shutdown")
def shutdown_db_client():
    disconnect("fast-api-database")

class Student(Document):
    name = StringField(required=True)
    student_number = IntField()

class Course(Document):
    name = StringField(required=True)
    description = StringField()
    tags = ListField(StringField())
    students = ListField(ReferenceField(Student, reverse_delete_rule=4))

class CourseData(BaseModel):
    name: str
    description: str | None
    tags: list[str] | None = []
    students: list[str] | None = []

class StudentData(BaseModel):
    name: str
    student_number: int | None


#
#
# COURSES 
#
#

@app.post("/courses", status_code=201)
def create_course(course: CourseData):
    new_course = Course(**course.dict()).save()
    response = {
        "message": "Course successfully created",
        "id": str(new_course.id)
    }
    return response

@app.get('/courses')
def get_courses(tag: str = None, studentName: str = None):
    query = {}
    if tag:
        query['tags'] = tag
    if studentName:
        student_ids = [student.id for student in Student.objects(name=studentName)]
        query['students__in'] = student_ids

    courses = Course.objects(**query)
    
    courses_list = []
    for course in courses:
        course_dict = json.loads(course.to_json())
        course_dict['id'] = str(course.id)
        del course_dict['_id']

        course_dict['students'] = [str(student.id) for student in course.students]

        courses_list.append(course_dict)

    return courses_list

@app.get('/courses/{course_id}')
def get_one_course(course_id: str):
    course = Course.objects.get(id=course_id)
    course_dict = json.loads(course.to_json())
    course_dict['id'] = str(course.id)
    del course_dict['_id']

    course_dict['students'] = [str(student.id) for student in course.students]

    return course_dict

@app.put("/courses/{course_id}")
def update_course(course_id: str, course: CourseData):
    course_data = course.dict()
    if "students" in course_data:
        course_data["students"] = [Student.objects.get(id=student_id) for student_id in course_data["students"]]
    try:
        Course.objects.get(id=course_id).update(**course_data)
        return {"message": "Course successfully updated"}
    except Course.DoesNotExist:
        raise HTTPException(status_code=404, detail="Course not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error")

@app.delete("/courses/{course_id}")
def delete_course(course_id: str):
    Course.objects(id=course_id).delete()
    return {"message" : "Course successfully deleted"}

#
#
# STUDENTS 
#
#

@app.post("/students", status_code=201)
def create_actor(student: StudentData):
    new_student = Student(**student.dict()).save()
    response = {
        "message": "Student successfully created",
        "id": str(new_student.id)
    }
    return response

@app.get('/students/{student_id}')
def get_one_student(student_id: str):
    try:
        student = Student.objects.get(id=student_id)
        student_dict = json.loads(student.to_json())
        student_dict['id'] = str(student.id)
        del student_dict['_id']
        return student_dict
    except Student.DoesNotExist:
        raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{student_id}")
def update_student(student_id: str, student_data: StudentData):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        raise HTTPException(status_code=404, detail="Student not found")

    student.update(**student_data.dict())
    return {"message": "Student successfully updated"}
   

@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    Student.objects(id=student_id).delete()
    return {"message" : "Student successfully deleted"}