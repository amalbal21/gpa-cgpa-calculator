from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import pandas as pd
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")

def load_subjects_from_excel():
    subjects = {}
    data_dir = "Artificial Intelligence and Data Science"
    # Sort filenames numerically to ensure correct semester order
    sorted_filenames = sorted(os.listdir(data_dir), key=lambda f: int(''.join(filter(str.isdigit, f)) or 0))
    for filename in sorted_filenames:
        if filename.endswith(".xlsx"):
            semester_name = filename.replace(".xlsx", "").capitalize()
            filepath = os.path.join(data_dir, filename)
            df = pd.read_excel(filepath)
            total_credits = int(df.iloc[-1]["Credits"])
            df = df.iloc[:-1]
            df['Credits'] = pd.to_numeric(df['Credits'], errors='coerce').fillna(0).astype(int)
            courses = []
            for index, row in df.iterrows():
                try:
                    course_name = row["Subject Name"]
                    credits = int(row["Credits"])
                    if pd.notna(course_name) and course_name != '':
                        courses.append({"name": course_name, "credits": credits})
                except (ValueError, TypeError) as e:
                    print(f"Skipping row {index} in {filename} due to error: {e}. Row data: {row}")
            subjects[semester_name] = {"courses": courses, "total_credits": total_credits}
    return subjects

# In-memory data for subjects and credits
SEMESTER_SUBJECTS = load_subjects_from_excel()

GRADE_POINTS = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'U': 0, 'W': 0, 'UA': 0, 'SA': 0}

class Course(BaseModel):
    grade: str
    credits: int

class GPARequest(BaseModel):
    courses: List[Course]

class Semester(BaseModel):
    semester: str
    gpa: float

class CGPARequest(BaseModel):
    semesters: List[Semester]

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/subjects")
async def get_subjects():
    return SEMESTER_SUBJECTS

@app.post("/calculate_gpa")
async def calculate_gpa_endpoint(gpa_request: GPARequest):
    total_points = 0
    total_credits = 0
    for course in gpa_request.courses:
        total_points += GRADE_POINTS.get(course.grade, 0) * course.credits
        total_credits += course.credits
    
    gpa = total_points / total_credits if total_credits > 0 else 0
    return {"gpa": gpa}

@app.post("/calculate_cgpa")
async def calculate_cgpa_endpoint(cgpa_request: CGPARequest):
    total_weighted_gpa = 0
    total_credits = 0
    for semester in cgpa_request.semesters:
        semester_credits = SEMESTER_SUBJECTS.get(semester.semester, {}).get("total_credits", 0)
        total_weighted_gpa += semester.gpa * semester_credits
        total_credits += semester_credits
    
    cgpa = total_weighted_gpa / total_credits if total_credits > 0 else 0
    return {"cgpa": cgpa}
