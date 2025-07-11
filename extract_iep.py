from textwrap import dedent
from pdf2image import convert_from_path
from collections import defaultdict
import os, json, boto3, base64

def convert_pdf_to_images(pdf_path, output_dir="images", dpi=200):
    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=dpi)
    image_paths = []
    for i, image in enumerate(images):
        path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(path, "PNG")
        image_paths.append(path)
    return image_paths

CLAUDE_IEP_PROMPT_TEMPLATE = dedent("""
    You are a special education document analyst reviewing an Individualized Education Program (IEP).

    Extract structured information about the student's support plan. Only use details that are **explicitly stated** in this chunk.

    Return the following fields under `student_profile_partial`:

    - `iep_goals`: list of annual goals described in the IEP
    - `accommodations`: list of instructional or testing accommodations. Be specific if it is pertaining to a certain subject, assessment, task, etc.
    - `services`: list of services provided to the student, each with:
        * `type` (e.g., "Specialized Academic Instruction", "Speech Therapy")
        * `frequency` (e.g., "2x/week", "500 minutes weekly")
        * `start_date` (if available, YYYY-MM-DD)
        * `end_date` (if available, YYYY-MM-DD)
    - `placement`: overall description of the student's placement (e.g., "General Education 80% or more", "Special Day Class")

    Only include fields if clearly mentioned in this chunk.

    Return only a valid JSON object parsable by `json.loads()` — no markdown, no commentary.

    {
    "student_profile_partial": {
        "iep_goals": ["..."],
        "accommodations": ["..."],
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
                                    
def call_claude_with_image(image_path, prompt_template):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.3,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/png", 
                        "data": image_base64
                    }},
                    {"type": "text", "text": prompt_template}
                ]
            }
        ]
    }
    response = bedrock.invoke_model(
        modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    response_body = json.loads(response["body"].read().decode("utf-8"))
    return response_body["content"][0]["text"]

def merge_student_profile_partials(partials):
    merged = {
        "iep_goals": [],
        "accommodations": [],
        "services": [],
        "placement": ""
    }
    seen = defaultdict(set)  
    for profile in partials:
        student = profile.get("student_profile_partial", {})
        for key in ["iep_goals", "accommodations"]:
            for item in student.get(key, []):
                if item not in seen[key]:
                    merged[key].append(item)
                    seen[key].add(item)
        for service in student.get("services", []):
            if service not in merged["services"]:
                merged["services"].append(service)
        placement = student.get("placement", "")
        if placement and len(placement) > len(merged["placement"]):
            merged["placement"] = placement
    return merged


def extract_student_info_from_iep(input_path):
    # 1. convert PDF to image pages bc claude doesn't take pdfs
    # 2. run claude on each image (page)
    # 3. merge all outputs (removing dupes) and save to file
    input_pdf = input_path
    output_dir = "images"
    image_paths = convert_pdf_to_images(input_pdf, output_dir=output_dir)
    print(f"Converted {len(image_paths)} pages to images.")
    all_outputs = []
    for img_path in image_paths:
        print(f"\nOutput for {img_path}:")
        result = call_claude_with_image(img_path, CLAUDE_IEP_PROMPT_TEMPLATE)
        print(result)
        try:
            parsed = json.loads(result)
            all_outputs.append(parsed)
        except Exception as e:
            print(f"Error parsing result for {img_path}: {e}")
            print("Raw output:", result)

    merged_profile = merge_student_profile_partials(all_outputs)
    with open("merged_iep_profile.json", "w", encoding="utf-8") as f:
        json.dump(merged_profile, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    input_pdf = "data/IEP_Redacted_Lawrence.pdf"
    extract_student_info_from_iep(input_pdf)
