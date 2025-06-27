import fitz 
import re
import boto3
import json

# pdf extraction utils
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def split_into_sections(text, headers):
    """given extracted text from student report and list of headers, 
    returns dict of chunks corresponding to each section"""
    pattern = '|'.join([re.escape(h) for h in headers])
    matches = list(re.finditer(pattern, text))
    sections = {}
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_title = match.group().strip().upper()
        section_content = text[start:end].strip()
        sections[section_title] = section_content
    return sections

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

