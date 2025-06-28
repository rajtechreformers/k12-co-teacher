import json
from utils import extract_text_from_pdf, split_into_sections, call_bedrock, get_pdf_paths

# TODO: 
# 2. streamlit ui interface for upload
# 3. being able to see the diff between original vs. generated modifications

def generate_lesson_modifications(sections):
    prompt = f"""
        You are an expert special education support assistant. Your task is to analyze a psychoeducational student report excerpt and identify key learning challenges, instructional needs, and recommend lesson modifications for a general education teacher.

        Here is the report excerpt you will be analyzing:

        <report_excerpt>
            --- INTERVIEWS ---
            {sections["INTERVIEWS"]}

            --- OBSERVATIONS ---
            {sections["OBSERVATIONS"]}

            --- CONCLUSION ---
            {sections["CONCLUSION"]}

            --- ELIGIBILITY ---
            {sections["ELIGIBILITY RECOMMENDATIONS AND CONSIDERATIONS"]}
        </report_excerpt>

        Before we begin the analysis, let's review the definitions of specific learning disabilities and other health impairments:

        <specific_learning_disability_definition>
            THESE DISABILITIES ARE NEUROLOGICAL IN ORIGIN AND IMPACT THE PROCESSES INVOLVED IN UNDERSTANDING OR USING SPOKEN OR WRITTEN LANGUAGE.
            These diabilities include:
            1. dyslexia
            2. disgarphia
            3. dyscalculia
            4. auditory processing disorder
            5. visual processing disorder
            6. nonverbal learning disorder
            7. executive functioning deficits
        </specific_learning_disabiliy_definition>

        <other_health_impaired_definition>
            THIS INCLUDES STUDENTS WHOSE HEALTH CONDITIONS SIGNIFICANTLY IMPACT THEIR STRENGTH, ENERGY, OR ALERTNESS,THEREBY AFFECTING THEIR EDUCATIONAL PERFORMANCE. BELOW ARE THE KEY AREAS COVERED UNDER OHI.
            1. Chronic or Acute Health Conditions (Asthma, Diabetes, Epilepsy, Heart conditions, Sickle cell anemia, Cancer)
            2. Attention Hyperactivity Disorder
            3. Tourette Syndrome
            4. Neurological Disorders (cerebal palsy, traumatic brain injury, multiple sclerosis)
            5. Autoimmune Disorders (Lupus, rheumatoid arthritis)
            6. Blood Disorders (hemophilia, leukemia)
            7. Chronic Fatigue or Energy Limitations (Chronic Fatigue Syndrome, fibromyalgia)
            8. Mental Health Conditions (emotional disturbance, anxiety, depression)
            9. Medical Fragility (Students with feeding tubes or oxygen dependency)
        </other_health_impaired_definition>

        Now, please analyze the report excerpt and identify the following:

        1. Key learning challenges or instructional needs of the student (e.g., "phonological_processing", "spelling_difficulty").
        2. Recommended lesson modifications (in plain English) that a general education teacher can implement.
        3. Identify specific learning disabilities, matching EXACTLY to the disabilities in the provided definition:
            - List evidence from the report that supports each potential diagnosis.
            - If no evidence from the ELIGIBILITY section aligns with the disabilities, leave this blank.
        4. Identify other health impairments, matching EXACTLY to the impairments in the provided definition:
            - List evidence from the report that supports each potential diagnosis.
            - If no evidence from the ELIGIBILITY section aligns with the impairments, leave this blank.
            

        Finally, present your analysis in a JSON format with the following structure:
        <output_format>
        {{
            "identified_disabilities_or_impairments": [
                {{
                    "type": "specific_learning_disability" or "other_health_impairment",
                    "name": "name of the disability or impairment",
                    "associated_needs": ["list of associated needs"],
                    "recommended_modifications": ["list of recommended modifications"]
                }}
            ]
        }}
        </output_format>
        
        Ensure that your response is only in the JSON format specified above, without any additional commentary. Each array should contain relevant items identified from the report excerpt. If no items are identified for a particular category, leave the array empty.

    """
    string_data = call_bedrock(prompt)
    print(string_data)
    try:
        return json.loads(string_data)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}

def build_final_lesson_plan(lesson_text, student_data):
    student_json_block = "\n".join(json.dumps(i, indent=2) for i in student_data)
    grouped_prompt = f"""
    You are a special education specialist tasked with creating individualized modifications for a lesson plan to support diverse learners. Your goal is to analyze student data and provide specific, categorized modifications that address each student's unique needs while maintaining the core objectives of the lesson.

    Follow these steps carefully:

    1. First, review the original lesson plan:
    <original_lesson_plan>
    {lesson_text}
    </original_lesson_plan>

    2. Here is the structured students data. Each entry contains the type of impairment, specific name, associated instructional needs, and recommended lesson modifications. Use this JSON structure directly:
    <student_data_json>
    {student_json_block}
    </student_data_json>

    3. Create modifications for the lesson plan based on the student's needs and recommended modifications. Focus on making the lesson more inclusive and accessible while maintaining its core objectives.

    4. Your output should consist of a new section titled "Modifications for Diverse Learners"

    5. In the "Modifications for Diverse Learners" section, organize your modifications into the following categories:
    - Instruction
    - Materials
    - Assessment
    - Participation
    - Environment/Technology (if applicable)

    6. Use bullet points and plain language for each modification.

    7. Format your response as follows:

    <output_format>
        Return only the content under the heading **Modifications for Diverse Learners**.
        Do not include any wrapping XML tags (like <response>), no brackets, and no placeholder phrases like "[Original lesson plan remains unchanged]".
        Your output should begin with "**Modifications for Diverse Learners**" and end with the last category.
        Nothing should come before or after this section.
        **Modifications for Diverse Learners**

        Instruction:
        - [Bullet point modification][type of disability or impairment]
        - [Bullet point modification][type of disability or impairment]

        Materials:
        - [Bullet point modification][type of disability or impairment]
        - [Bullet point modification][type of disability or impairment]

        Assessment:
        - [Bullet point modification][type of disability or impairment]
        - [Bullet point modification][type of disability or impairment]

        Participation:
        - [Bullet point modification][type of disability or impairment]
        - [Bullet point modification][type of disability or impairment]

        Environment/Technology (if applicable):
        - [Bullet point modification][type of disability or impairment]
        - [Bullet point modification][type of disability or impairment]

    </output_format>

    Remember to tailor the modifications to address the specific needs of the student while ensuring they align with the lesson's objectives and standards.

    """
    return call_bedrock(grouped_prompt)

def process_student_reports(reports, original_lesson_txt):
    """takes in a list of student IEP's and generates a modified lesson plan"""
    student_modifications = []
    section_labels = [
        "REASON FOR REFERRAL", "ASSESSMENT TOOLS", "ASSESSMENT GUIDELINES AND CONSIDERATIONS",
        "BACKGROUND INFORMATION", "DEVELOPMENT, HEARING, AND VISION", "PREVIOUS ASSESSMENTS",
        "CURRENT PLACEMENT/GOALS/SUPPLEMENTARY AIDS/RELATED SERVICES", "INTERVENTIONS",
        "INTERVIEWS", "OBSERVATIONS", "ASSESSMENT INFORMATION", "SCORING GUIDELINES",
        "OVERALL COGNITIVE SKILLS", "PROCESSING SKILLS", "SOCIAL-EMOTIONAL, BEHAVIORAL, AND ADAPTIVE SKILLS",
        "ORAL LANGUAGE ASSESSMENT", "ACADEMIC SKILLS", "CONCLUSION", "ELIGIBILITY RECOMMENDATIONS AND CONSIDERATIONS"
    ]
    for report in reports:
        report_text = extract_text_from_pdf(report)
        print("Extracted text from student report...")
        sections = split_into_sections(report_text, section_labels)
        modifications = generate_lesson_modifications(sections)
        student_modifications.append(modifications)
    final_plan = build_final_lesson_plan(lesson_text, student_modifications)
    with open("new_lesson_plan_all_students.txt", "w", encoding="utf-8") as f:
        f.write(lesson_text)
        f.write("\n")
        f.write(final_plan)

if __name__ == "__main__":
    reports = get_pdf_paths("reports")
    lesson_text = extract_text_from_pdf("data/Madelyn_Hunter_Calculus.pdf")
    print("Extracted text from lesson plan...")
    process_student_reports(reports, lesson_text)
    print("Modified lesson plan successfully generated!")
   

