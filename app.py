import streamlit as st
from lesson_modifier import process_student_reports
import os
# 1. take in a single lesson plan
# 2. take in one or more student files
# 3. modify the lesson plan and output it
# 4. if more IEPs are uploaded edit it more.

st.title('Lesson Plan Modifer')
student_files = st.file_uploader(
    "please upload student IEP files here", accept_multiple_files=True, type=["pdf"]
)
lesson_plan = st.file_uploader(
    "please upload the lesson plan you plan on modifying here", type=["pdf"]
)
student_reports_path = "student_reports"
# saving student report files to local dir
os.makedirs(student_reports_path, exist_ok=True)
if student_files:
    st.success(f"{len(student_files)} student files uploaded!")
    for uploaded_file in student_files:
        students_file_path = os.path.join(student_reports_path, uploaded_file.name)
        bytes_data = uploaded_file.read()
        with open(students_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.write(f"saved: {students_file_path}")
# saving lesson plan files to local dir
lesson_path = "lesson_plans"
os.makedirs(lesson_path, exist_ok=True)
if lesson_plan:
    st.success("lesson plan successfully uploaded!")
    lesson_file_path = os.path.join(lesson_path, lesson_plan.name)
    bytes_data = lesson_plan.read()
    with open(lesson_file_path, "wb") as f:
        f.write(lesson_plan.getbuffer())
        st.write(f"saved: {lesson_file_path}")

    




