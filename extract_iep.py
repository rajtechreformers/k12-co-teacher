from claude_extract import prepare_claude_chunks
from textwrap import dedent

# IEPs contain all tables
# need to extract tables using textract or something else
chunks = prepare_claude_chunks("data/IEP_Redacted_Lawrence.pdf", 1)
print(f"There are {len(chunks)} chunks found in this report")
with open("iep.txt", "w", encoding="utf-8") as f:
    for i, chunk in enumerate(chunks):
        f.write(chunk)

CLAUDE_IEP_PROMPT_TEMPLATE = dedent("""
    You are a special education document analyst reviewing an Individualized Education Program (IEP).

    Extract structured information about the student’s support plan. Only use details that are **explicitly stated** in this chunk.

    Return the following fields under `student_profile_partial`:

    - `iep_goals`: list of annual goals described in the IEP
    - `accommodations`: list of instructional or testing accommodations
    - `learning_styles`: list of learning preferences or styles if stated (optional)
    - `services`: list of services provided to the student, each with:
        * `type` (e.g., "Specialized Academic Instruction", "Speech Therapy")
        * `frequency` (e.g., "2x/week", "500 minutes weekly")
        * `start_date` (if available, YYYY-MM-DD)
        * `end_date` (if available, YYYY-MM-DD)
    - `placement`: overall description of the student’s placement (e.g., "General Education 80% or more", "Special Day Class")

    Only include fields if clearly mentioned in this chunk.

    Return only a valid JSON object parsable by `json.loads()` — no markdown, no commentary.

    {
    "student_profile_partial": {
        "iep_goals": ["..."],
        "accommodations": ["..."],
        "learning_styles": ["..."],
        "services": [
        {
            "type": "Speech and Language Services",
            "frequency": "1x/week for 30 minutes",
            "start_date": "2024-10-01",
            "end_date": "2025-06-01"
        }
        ],
        "placement": "General Education 80% or more"
    }
    }

    Here is the raw text:
    ---
    {{CHUNK}}
""")
                                    
                                    
