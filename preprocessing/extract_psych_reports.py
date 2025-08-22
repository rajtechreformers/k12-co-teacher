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
        # print(chunk_text)
        chunks.append(dedent(chunk_text.strip()))
    return chunks

def load_prompt_with_chunk(path, chunk_text):
    with open(path, "r", encoding="utf-8") as f:
        raw_prompt = f.read()
    filled_prompt = raw_prompt.replace("{{CHUNK}}", chunk_text)
    return dedent(filled_prompt)

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
def extract_psychological_report(path_to_report, student_id):
    chunks = prepare_claude_chunks(path_to_report)
    print(f"There are {len(chunks)} chunks found in this report")
    os.makedirs(student_id, exist_ok=True)
    with open(f"{student_id}/psych_report.txt", "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(chunk)

    os.makedirs(f"{student_id}/claude_outputs", exist_ok=True)
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        prompt = load_prompt_with_chunk("prompts/claude3.5_psych_prompt.txt", chunk)
        try:
            response = call_bedrock(prompt)
            # print(f"RAW RESPONSE for chunk {i+1}:\n{response[:500]}\n")
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            parsed = json.loads(response[json_start:json_end])
            with open(f"{student_id}/claude_outputs/chunk_{i+1:02d}.json", "w") as f:
                json.dump(parsed, f, indent=2)
            print(f"Chunk {i+1} saved.") 
        except Exception as e:
            print(f"Error on chunk {i+1}:", e)
    merge_student_profiles("claude_outputs", student_id=student_id, output_path=f"{student_id}/{student_id}_student_profile.json")

if __name__ == "__main__":
    student_id = str(uuid.uuid4())
    extract_psychological_report("data/SLD Report.pdf", student_id)
