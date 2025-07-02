from pathlib import Path
import fitz 
import re
import boto3
import json
import os

# pdf extraction utils
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "".join([page.get_text() for page in doc])

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

def get_pdf_paths(directory):
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(".pdf")
    ]

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

# html formatting functions
def extract_metadata(text):
    """extracts the header section of the lesson plan"""
    meta = {
        "teacher": "",
        "date": "",
        "subject": "",
        "grade": ""
    }
    lines = text.splitlines()
    for line in lines:
        if line.startswith("Teacher:"):
            meta["teacher"] = line.split(":", 1)[1].strip()
        elif line.startswith("Date:"):
            meta["date"] = line.split(":", 1)[1].strip()
        elif line.startswith("Subject Area:"):
            meta["subject"] = line.split(":", 1)[1].strip()
        elif line.startswith("Grade Level:"):
            meta["grade"] = line.split(":", 1)[1].strip()
    return meta

def extract_sections(text):
    """extractions lesson plan into sections w/ corr content for html construction later """
    # match on either:
    # 1. title case + colon w/ optional trailing spaces ("Objective Purpose:")
    # 2. all CAPS with optional trailing spaces ("OBJECTIVE PURPOSE")
    pattern = re.compile(r'^([A-Z][A-Za-z\s/]+:|[A-Z\s]{5,})$', re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections = []
    for i, match in enumerate(matches):
        title = match.group(1).strip().rstrip(":")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append({"title": title, "content": content})
    return sections

def render_html(metadata, sections, output_path="lesson_plan.html"):
    # currently just taking the original <style> from the sample lesson
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>Madelyn Hunter Lesson Plan</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                        .lesson-plan {{ background-color: white; border: 2px solid #333; max-width: 800px; margin: 0 auto; }}
                        .header {{ background-color: #e8e8e8; padding: 10px; text-align: center; font-weight: bold; font-size: 18px; }}
                        .info-row {{ display: flex; border-bottom: 1px solid #333; }}
                        .info-cell {{ flex: 1; padding: 8px; border-right: 1px solid #333; }}
                        .info-cell:last-child {{ border-right: none; }}
                        .section {{ border-bottom: 1px solid #333; padding: 10px; }}
                        .section:last-child {{ border-bottom: none; }}
                        .section-title {{ font-weight: bold; margin-bottom: 5px; }}
                        .section-description {{ font-style: italic; font-size: 12px; color: #666; margin-bottom: 10px; }}
                        .section-content {{ line-height: 1.4; white-space: pre-wrap; }}
                    </style>
                </head>
                <body>
                    <div class="lesson-plan">
                        <div class="header">Madelyn Hunter Lesson Cycle - Lesson Plan Template</div>
                        <div class="info-row">
                            <div class="info-cell"><strong>Teacher:</strong> {metadata['teacher']}</div>
                            <div class="info-cell"><strong>Date:</strong> {metadata['date']}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-cell"><strong>Subject Area:</strong> {metadata['subject']}</div>
                            <div class="info-cell"><strong>Grade Level:</strong> {metadata['grade']}</div>
                        </div>
            """)
        # continue adding to <body> by adding in the sections
        for sec in sections:
            sec_content = sec['content'].replace('\n', '<br>')
            f.write(f"""
                <div class="section">
                    <div class="section-title">{sec['title']}:</div>
                    <div class="section-content">{sec_content}</div>
                </div>
                """)
        f.write("</div></body></html>")

def convert_to_html(mod_lesson_path, designated_file_name):
    text = Path(mod_lesson_path).read_text()
    meta = extract_metadata(text)
    sections = extract_sections(text)
    render_html(meta, sections, designated_file_name)


# convert_to_html("new_lesson_plan_all_students.txt", "madelyn_hunter_generated.html")

    



