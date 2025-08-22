from textwrap import dedent
from pdf2image import convert_from_path
from collections import defaultdict
import os, json, boto3, base64, uuid

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

CLAUDE_IEP_PROMPT= dedent(load_prompt("prompts/claude3.5_iep_prompt.txt"))    

def convert_pdf_to_images(pdf_path, output_dir="images", dpi=200):
    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=dpi)
    image_paths = []
    for i, image in enumerate(images):
        path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(path, "PNG")
        image_paths.append(path)
    return image_paths

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


def extract_student_info_from_iep(input_path, student_id):
    # 1. convert PDF to image pages bc claude doesn't take pdfs
    # 2. run claude on each image (page)
    # 3. merge all outputs (removing dupes) and save to file
    input_pdf = input_path
    output_dir = f"{student_id}/images"
    image_paths = convert_pdf_to_images(input_pdf, output_dir=output_dir)
    print(f"Converted {len(image_paths)} pages to images.")
    all_outputs = []
    for img_path in image_paths:
        print(f"\nOutput for {img_path}:")
        result = call_claude_with_image(img_path, CLAUDE_IEP_PROMPT)
        print(result)
        try:
            parsed = json.loads(result)
            all_outputs.append(parsed)
        except Exception as e:
            print(f"Error parsing result for {img_path}: {e}")
            print("Raw output:", result)

    merged_profile = merge_student_profile_partials(all_outputs)
    with open(f"{student_id}/{student_id}_merged_iep_profile.json", "w", encoding="utf-8") as f:
        json.dump(merged_profile, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    input_pdf = "data/IEP_Redacted_Johansson.pdf"
    student_id = str(uuid.uuid4())
    extract_student_info_from_iep(input_pdf, student_id)
