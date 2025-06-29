import streamlit as st
from lesson_modifier import modify_lesson_plan
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

# create folders
student_reports_path = "student_reports"
os.makedirs(student_reports_path, exist_ok=True)
lesson_path = "lesson_plans"
os.makedirs(lesson_path, exist_ok=True)

# saving student report files to local dir
student_file_paths = []
if student_files:
    st.success(f"{len(student_files)} student files uploaded!")
    for uploaded_file in student_files:
        students_file_path = os.path.join(student_reports_path, uploaded_file.name)
        student_file_paths.append(students_file_path)
        bytes_data = uploaded_file.read()
        with open(students_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.write(f"saved: {students_file_path}")

# saving lesson plan files to local dir
if lesson_plan:
    st.success("lesson plan successfully uploaded!")
    lesson_file_path = os.path.join(lesson_path, lesson_plan.name)
    bytes_data = lesson_plan.read()
    with open(lesson_file_path, "wb") as f:
        f.write(lesson_plan.getbuffer())
        st.write(f"saved: {lesson_file_path}")

# modifying lesson plan based on students' needs
if student_files and lesson_plan:
    st.write("Modifying lesson plan ...")
    modify_lesson_plan(student_file_paths, lesson_file_path)
    modified_lesson_path = "new_lesson_plan_all_students.txt"

    if os.path.exists(modified_lesson_path):
        with open(modified_lesson_path, "r", encoding="utf-8") as f:
            modified_text = f.read()
        st.subheader("Modified Lesson Plan")
        st.text_area("Preview:", modified_text, height=400)



    



    




