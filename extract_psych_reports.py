from textwrap import dedent
from collections import defaultdict
from pathlib import Path
import fitz, json, os, uuid, boto3

# invoke bedrock
def call_bedrock(prompt, model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0"):
    bedrock = boto3.client(service_name="bedrock-runtime", region_name="us-west-2")
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 5000,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]
    except Exception as e:
        print("call to bedrock failed", e)
        raise

def extract_text_blocks_from_pdf(pdf_path):
    import fitz
    doc = fitz.open(pdf_path)
    page_texts = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))  # order: top-down, then left-right
        cleaned_blocks = [b[4].strip() for b in blocks if b[4].strip()]
        page_text = "\n\n".join(cleaned_blocks)
        page_texts.append((page_num + 1, page_text))
    return page_texts

def extract_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    image_info = []
    for i, page in enumerate(doc):
        images = page.get_images(full=True)
        if images:
            image_info.append({"page": i + 1, "num_images": len(images)})
    return image_info

def prepare_claude_chunks(pdf_path, pages_per_chunk=5):
    text_blocks = extract_text_blocks_from_pdf(pdf_path)
    image_pages = {info["page"] for info in extract_images_from_pdf(pdf_path)}
    chunks = []
    for i in range(0, len(text_blocks), pages_per_chunk):
        chunk_pages = text_blocks[i:i+pages_per_chunk]
        chunk_text = ""
        for page_num, text in chunk_pages:
            chunk_text += f"\n---\nPage {page_num}:\n{text.strip()}\n"
            if page_num in image_pages:
                chunk_text += f"\n[Image Placeholder: Page {page_num} contains a diagram, table, or visual.]\n"
        print(chunk_text)
        chunks.append(dedent(chunk_text.strip()))
    return chunks


# TODO: improve prompt to better detect OHI 
CLAUDE_PROMPT_TEMPLATE = dedent("""
    You are a special education document analyst reviewing a student psychological evaluation report used for IEP planning.

    Below are the official definitions of disability categories. Use them strictly to match and identify any impairments mentioned in the report.

    ---

    <specific_learning_disability_definition>
        THESE DISABILITIES ARE NEUROLOGICAL IN ORIGIN AND IMPACT THE PROCESSES INVOLVED IN UNDERSTANDING OR USING SPOKEN OR WRITTEN LANGUAGE.
        These disabilities include:
        1. dyslexia
        2. dysgraphia
        3. dyscalculia
        4. auditory processing disorder
        5. visual processing disorder
        6. nonverbal learning disorder
        7. executive functioning deficits
    </specific_learning_disability_definition>

    <other_health_impaired_definition>
        THIS INCLUDES STUDENTS WHOSE HEALTH CONDITIONS SIGNIFICANTLY IMPACT THEIR STRENGTH, ENERGY, OR ALERTNESS, THEREBY AFFECTING THEIR EDUCATIONAL PERFORMANCE. BELOW ARE THE KEY AREAS COVERED UNDER OHI:
        1. Chronic or Acute Health Conditions (Asthma, Diabetes, Epilepsy, Heart conditions, Sickle cell anemia, Cancer)
        2. Attention Hyperactivity Disorder (ADHD)
        3. Tourette Syndrome
        4. Neurological Disorders (cerebral palsy, traumatic brain injury, multiple sclerosis)
        5. Autoimmune Disorders (Lupus, rheumatoid arthritis)
        6. Blood Disorders (hemophilia, leukemia)
        7. Chronic Fatigue or Energy Limitations (Chronic Fatigue Syndrome, fibromyalgia)
        8. Mental Health Conditions (emotional disturbance, anxiety, depression)
        9. Medical Fragility (Students with feeding tubes or oxygen dependency)
    </other_health_impaired_definition>

    ---

    Please do the following:
    1. Extract a list of all section headings you identify, keeping their **EXACT** original titles as shown in the report.
    2. Identify which section headings are **KEY for IEP decision-making**, focusing on:
    - Cognitive assessment
    - Academic performance
    - Social-emotional status
    - Health/medical info
    - Recommendations
    - Eligibility statements

    3. Build a `student_profile_partial` object using ONLY what is mentioned in this chunk. 
    Extract:
    - first_name (or null)
    - last_name (or null)
    - student_id (UUID or null)
    - iep_goals (list)
    - accommodations (list)
    - learning_styles (list)
    - `disabilities`: A list of objects each with:
        * `type`: must be `"specific_learning_disability"` or `"other_health_impairment"`
        * `name`: must match exactly one of the 16 official categories defined above
        * Only include if there is **explicit evidence** from sections on **ELIGIBILITY RECOMMENDATIONS AND CONSIDERATIONS** sections that the student is **identified with** or **meets criteria for** that condition.
        * Look for language such as “meets criteria for…”, “is eligible under…”, or “is identified with…” — do not include vague or speculative mentions.
    - interviews (dict with keys: teacher, parent) with overall interview information that would be helpful to know in the student profile.
    - observations (dict with key: psychologist) with overall summary of the psychologist's observation of student.

    4. For `key_iep_sections`, only use the **exact section titles** found in the document — do not reword or shorten.
    
    Return only a valid JSON object, directly parsable by Python `json.loads()` — no markdown, no extra commentary.
    {
        "key_iep_sections": {
            "RECOMMENDATIONS": "...",
            "COGNITIVE ASSESSMENT": "..."
        },
        "student_profile_partial": {
            "first_name": null,
            "last_name": null,
            "student_id": null,
            "iep_goals": ["..."],
            "accommodations": ["..."],
            "learning_styles": ["..."],
            "disabilities": [
                {
                    "type": "specific_learning_disability" //[if applicable and mentioned],
                    "name": "Dyslexia" 
                },
                {
                    "type": "other_health_impairment" //[if applicable and mentioned],
                    "name": "Attention Hyperactivity Disorder (ADHD)"
                
                }
            ],
            "interviews": {
                "teacher": "Teachers described STUDENT as a kind, calm, happy, creative, eager to answer, and distracted child. They reported her strengths as creativity, kindness, motivation, working well with others, and self-advocacy.",
                "parent": "Parent described STUDENT as sweet, kind, and artistic. Parent reported that STUDENT loves to read and draw. She reported that STUDENT is curious and wants to learn. She loves art and creative classes. "
            },
            "observations": {
                "psychologist": "STUDENT was observed during her language arts and math classes. She was observed to struggle to follow directions given, missing details in the information presented. Likewise, she required staff prompting for on-task behavior. Socially, she was observed interacting with peers and seeking peer interactions. During assessment sessions, STUDENT was observed to struggle with focus and attention, seeking items to fidget with and requiring prompting for on-task behavior"
            }
        }
    }

    Here is the raw text:
    ---
    {{CHUNK}}

""")                                

def merge_claude_results(json_outputs_dir, output_dir="final_outputs"):
    os.makedirs(output_dir, exist_ok=True)
    # all_headings = set()
    key_iep = defaultdict(str)
    for path in sorted(Path(json_outputs_dir).glob("chunk_*.json")):
        with open(path, "r") as f:
            data = json.load(f)        
        for key, val in data.get("key_iep_sections", {}).items():
            key_iep[key] += val.strip() + "\n"
    # Path(output_dir, "all_section_headings.json").write_text(json.dumps(sorted(all_headings), indent=2))
    Path(output_dir, "key_iep_sections.json").write_text(json.dumps(key_iep, indent=2))


def merge_student_profiles(json_outputs_dir, student_id="xxxx", output_path="final_outputs/student_profile.json"):
    """
    input: output dir for resulting student profile json, output file path for student profile json
    output: nothing

    this function extracts student profile specific info into a student profile json across all the jsons produced for each chunk passed to claude

    """
    os.makedirs(Path(output_path).parent, exist_ok=True)
    profile = {
        "student_id": None,
        "first_name": None,
        "last_name": None,
        "disabilities": [],
        "iep_goals": [],
        "accommodations": [],
        "learning_styles": [],
        "interviews":{},
        "observations": {}
    }

    ALLOWED_SPECIFIC_LEARNING_DISABILITIES = {
        "dyslexia",
        "dysgraphia",
        "dyscalculia",
        "auditory processing disorder",
        "visual processing disorder",
        "nonverbal learning disorder",
        "executive functioning deficits"
    }

    ALLOWED_OTHER_HEALTH_IMPAIRMENTS = {
        "chronic or acute health conditions",
        "attention hyperactivity disorder (adhd)",
        "tourette syndrome",
        "neurological disorders",
        "autoimmune disorders",
        "blood disorders",
        "chronic fatigue or energy limitations",
        "mental health conditions",
        "medical fragility"
    }

    seen_disabilities = set()
    # merging info from each chunk_*json file
    for path in sorted(Path(json_outputs_dir).glob("chunk_*.json")):
        with open(path) as f:
            data = json.load(f)
            partial = data.get("student_profile_partial", {})

        for field in ["first_name", "last_name", "student_id"]:
            if not profile[field] and partial.get(field):
                profile[field] = partial[field]

        profile["iep_goals"].extend(partial.get("iep_goals", []))
        profile["accommodations"].extend(partial.get("accommodations", []))
        profile["learning_styles"].extend(partial.get("learning_styles", []))

        for role, text in partial.get("interviews", {}).items():
            if role not in profile["interviews"]:
                profile["interviews"][role] = text
        for role, text in partial.get("observations", {}).items():
            if role not in profile["observations"]:
                profile["observations"][role] = text

        # Merge disabilities filtering for any duplication/'none'
        for d in partial.get("disabilities", []):
            name = d.get("name")
            type = d.get("type")
            if not name or not type:
                continue  
            name = name.strip().lower()
            type = type.strip().lower()
            if (
                (type == "specific_learning_disability" and name in ALLOWED_SPECIFIC_LEARNING_DISABILITIES) or
                (type == "other_health_impairment" and name in ALLOWED_OTHER_HEALTH_IMPAIRMENTS)
            ):
                key = (type, name)
                if key not in seen_disabilities:
                    seen_disabilities.add(key)
                    profile["disabilities"].append({
                        "type": type,
                        "name": name
                    })

    # sort + remove any duplicates found across chunks 
    profile["iep_goals"] = sorted(set(profile["iep_goals"]))
    profile["accommodations"] = sorted(set(profile["accommodations"]))
    profile["learning_styles"] = sorted(set(profile["learning_styles"]))

    # generating student UUID for now 
    # TODO: change this to actual id's in the future
    profile["student_id"] = student_id

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"Merged student profile saved to {output_path}")


# execution  ---------------
# 1. extract txt and denote img place holders using pypdf 
# 2. feed claude extracted output, chunk by chunk
# 3. claude generates json partial student profile from each chunk
# 4. merge all partial student json profiles into a final student profile
def extract_psychological_report(path_to_report="reports/SLD Report.pdf"):
    chunks = prepare_claude_chunks(path_to_report)
    print(f"There are {len(chunks)} chunks found in this report")
    with open("pypdf.txt", "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(chunk)

    os.makedirs("claude_outputs", exist_ok=True)
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        prompt = CLAUDE_PROMPT_TEMPLATE.replace("{{CHUNK}}", chunk)
        try:
            response = call_bedrock(prompt)
            # print(f"RAW RESPONSE for chunk {i+1}:\n{response[:500]}\n")
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            parsed = json.loads(response[json_start:json_end])
            with open(f"claude_outputs/chunk_{i+1:02d}.json", "w") as f:
                json.dump(parsed, f, indent=2)
            print(f"Chunk {i+1} saved.") 
        except Exception as e:
            print(f"Error on chunk {i+1}:", e)
    # merge_claude_results("claude_outputs", output_dir="final_outputs")

    student_id = str(uuid.uuid4())
    merge_student_profiles("claude_outputs", student_id=student_id, output_path=f"final_outputs/{student_id}_student_profile.json")

# extract_psychological_report()