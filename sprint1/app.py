import os
import streamlit as st
import streamlit.components.v1 as components
import uuid
from sprint1.lesson_modifier import modify_lesson_plan
from sprint1.utils import convert_to_html
from weasyprint import HTML

st.title("📝 Lesson Plan Modifier")
st.markdown("""
Upload a general education **lesson plan** and one or more **IEP student reports**.
The system will modify the lesson plan to include differentiated supports for each student.
""")
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

# saving lesson plan files to local dir
if lesson_plan:
    st.success("lesson plan successfully uploaded!")
    lesson_file_path = os.path.join(lesson_path, lesson_plan.name)
    bytes_data = lesson_plan.read()
    with open(lesson_file_path, "wb") as f:
        f.write(lesson_plan.getbuffer())

# modifying lesson plan based on students' needs
if student_files and lesson_plan:
    modified_lesson_path = "modified_lesson.txt"
    output_file = modified_lesson_path
    with st.spinner("Modifying lesson plan ..."):
        student_modifications = modify_lesson_plan(student_file_paths, lesson_file_path, output_file)
    
    # using fake student data for now
    # displaying students + corrs disabilities and modifications
    names = ["April Chan", "May Smith"]
    names_to_modifications = {}
    for i in range(len(student_modifications)):
        names_to_modifications[names[i]] = student_modifications[i]
    st.markdown("## 🧑‍🎓 Student-Specific Modifications")
    for student_name, student_data in names_to_modifications.items():
        with st.expander(f"{student_name}", expanded=False):
            for disability in student_data.get("identified_disabilities_or_impairments", []):
                st.markdown(
                    f"<h2>{disability['name'].title()}</h2><p>({disability['type'].replace('_', ' ').title()})</p>",
                    unsafe_allow_html=True
                )
                st.markdown("Recommended Modifications:", unsafe_allow_html=True)
                mod_list = "".join([f"<li>{mod}</li>" for mod in disability["recommended_modifications"]])
                st.markdown(f"<ul>{mod_list}</ul>", unsafe_allow_html=True)

    if os.path.exists(modified_lesson_path):
        with open(modified_lesson_path, "r", encoding="utf-8") as f:
            modified_text = f.read()
        st.subheader("Modified Lesson Plan")
        # generate html for lesson plan
        modified_lesson_html = f"modified_lesson{uuid.uuid4()}.html"
        with st.spinner("Converting lesson plan to HTML..."):
            convert_to_html(modified_lesson_path, modified_lesson_html)
        with open(modified_lesson_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=700, scrolling=True)
        HTML(modified_lesson_html).write_pdf("modified_lesson.pdf")
        st.download_button("download PDF", 
                           open("modified_lesson.pdf", "rb").read(),
                           file_name="modified_lesson.pdf", 
                           mime="application/pdf")



    




