import os
import streamlit as st
import streamlit.components.v1 as components
import uuid
from lesson_modifier import modify_lesson_plan
from utils import convert_to_html

# 1. take in a single lesson plan
# 2. take in one or more student files
# 3. modify the lesson plan and output it
# 4. if more IEPs are uploaded it should modify the existing lesson plan file.

st.title("📝 Lesson Plan Modifier")
with st.expander("📥 Upload Your Files", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        lesson_plan = st.file_uploader(
            "Upload a Lesson Plan", type=["pdf"]
        )
    with col2:
        student_files = st.file_uploader(
            "Upload IEPs (1 or more) here", accept_multiple_files=True, type=["pdf"]
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
    modified_lesson_path = "modified_lesson.txt"
    output_file = modified_lesson_path
    st.write("Modifying lesson plan ...")
    modify_lesson_plan(student_file_paths, lesson_file_path, output_file)
    
    if os.path.exists(modified_lesson_path):
        with open(modified_lesson_path, "r", encoding="utf-8") as f:
            modified_text = f.read()
        st.subheader("Modified Lesson Plan")
        # generate html for lesson plan
        modified_lesson_html = f"modified_lesson{uuid.uuid4()}.html"
        st.write("Converting lesson plan to html ...")
        convert_to_html(modified_lesson_path, modified_lesson_html)
        with open(modified_lesson_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=700, scrolling=True)



    



    




