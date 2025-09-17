from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import pandas as pd
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")

def get_departments():
    # Exclude .idea, __pycache__, and other non-department folders
    excluded_folders = ['.idea', '__pycache__', 'templates', '.git']
    # Also exclude files
    excluded_files = ['gpa_calculator.py', 'main.py', 'Procfile', 'requirements.txt']
    
    departments = [item for item in os.listdir('.') if os.path.isdir(item) and item not in excluded_folders]
    return departments

def load_subjects_from_excel(department: str):
    subjects = {}
    data_dir = department
    if not os.path.isdir(data_dir):
        raise HTTPException(status_code=404, detail="Department not found")

    try:
        # Sort filenames numerically to ensure correct semester order
        sorted_filenames = sorted(os.listdir(data_dir), key=lambda f: int(''.join(filter(str.isdigit, f)) or 0))
    except (FileNotFoundError, ValueError):
        # Handle cases where the directory is empty or contains non-standard filenames
        return {}

    for filename in sorted_filenames:
        if filename.endswith(".xlsx"):
            semester_name = filename.replace(".xlsx", "").capitalize()
            filepath = os.path.join(data_dir, filename)
            try:
                df = pd.read_excel(filepath)
                # Check if the required columns are present
                if "Subject Name" not in df.columns or "Credits" not in df.columns:
                    print(f"Skipping file {filename} due to missing 'Subject Name' or 'Credits' column.")
                    continue

                # Find the row with "Total" in any column to identify the total credits row
                total_row_mask = df.apply(lambda row: row.astype(str).str.contains('Total', case=False).any(), axis=1)
                if total_row_mask.any():
                    total_credits_row = df[total_row_mask].iloc[0]
                    total_credits = int(total_credits_row["Credits"])
                    df = df[~total_row_mask] # Exclude total row from subjects
                else:
                    total_credits = 0 # Default if no total row is found
                
                # Fix for incorrect credits in Artificial Intelligence And Data Science/Semester 2.xlsx
                if department == "Artificial Intelligence And Data Science" and semester_name == "Semester 2":
                    df.loc[df['Subject Code'] == '24CS2101', 'Credits'] = 4
                    total_credits = 25

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
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
    return subjects


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
    department: str

@app.get("/", response_class=HTMLResponse)
async def get_welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

@app.get("/departments")
async def list_departments():
    return get_departments()

@app.get("/{department}", response_class=HTMLResponse)
async def get_index(request: Request, department: str):
    # To make sure the department exists before rendering the page
    if department not in get_departments():
        raise HTTPException(status_code=404, detail="Department not found")
    return templates.TemplateResponse("index.html", {"request": request, "department": department})

@app.get("/subjects/{department}")
async def get_subjects(department: str):
    return load_subjects_from_excel(department)

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
    
    department_subjects = load_subjects_from_excel(cgpa_request.department)

    for semester in cgpa_request.semesters:
        semester_info = department_subjects.get(semester.semester, {})
        semester_credits = semester_info.get("total_credits", 0)
        total_weighted_gpa += semester.gpa * semester_credits
        total_credits += semester_credits
    
    cgpa = total_weighted_gpa / total_credits if total_credits > 0 else 0
    return {"cgpa": cgpa}