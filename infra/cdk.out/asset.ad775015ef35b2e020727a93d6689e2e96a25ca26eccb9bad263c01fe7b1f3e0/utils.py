import boto3
import json
import urllib3

http = urllib3.PoolManager()
def post_json(url, payload):
    r = http.request(
        "POST",
        url,
        body=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    return json.loads(r.data)

# CLAUDE HELPERS ==========================

def format_history_for_claude(messages):
    # sort by teimstamp
    sorted_messages = sorted(messages, key=lambda x: int(x["created_at"]))
    claude_messages = []
    for msg in sorted_messages:
        role = "user" if msg["sender"].lower() == "user" else "assistant"
        text = msg.get("message", "")
        claude_messages.append({
            "role": role,
            "content": [{"text": text}]
        })
    return claude_messages

def load_prompt_template(filepath, replacements):
    with open(filepath, "r") as f:
        template = f.read()
    for key, value in replacements.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template

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
