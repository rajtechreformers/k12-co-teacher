import json
import boto3
import uuid
from conversation_history import *
from student_utils import *
from utils import *
import os

bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-west-2')

def lambda_handler(event, context):
    if event['requestContext']['routeKey'] == '$connect':
        return {'statusCode': 200}
    
    if event['requestContext']['routeKey'] == '$disconnect':
        return {'statusCode': 200}

    print(f"Event: {event}")
    print(f"Context: {context}")
    
    try:
        # Parse request
        message_data = json.loads(event.get("body", "{}"))
        body = message_data.get("body") 
        teacher_id = message_data.get("teacherId")
        session_id = message_data.get("sessionId")
        student_ids = message_data.get("studentIDs", [])
        class_id = message_data.get("classId", "")

        chat_type = "student" if len(student_ids) == 1 else "general"

        print(f"Teacher ID: {teacher_id}")
        print(f"Session ID: {session_id}")
        print(f"Student IDs: {student_ids}")
        print(f"Chat Type: {chat_type}")

        domain = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        api_endpoint = f"https://{domain}/{stage}"

        apigw_client = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=api_endpoint
        )

        if not body or not teacher_id:
            return {'statusCode': 400, 'body': 'Missing body or teacherId'}

        # New conversation
        is_new_convo = session_id is None
        if is_new_convo:
            session_id = str(uuid.uuid4())
            try:
                create_conversation(
                    user_id=teacher_id,
                    conversation_attributes={
                        "conversation_id": session_id,
                        "title": "",
                        "type": chat_type,
                        "student_ids": student_ids,
                        "class_id": class_id
                    }
                )
            except Exception as e:
                print(f"Error creating conversation: {e}")
                return {'statusCode': 500, 'body': 'Error creating conversation'}
        
        # Save user message
        try:
            create_chat_message(
                user_id=teacher_id,
                conversation_id=session_id,
                message=body,
                sender="user"
            )
        except Exception as e:
            print(f"Error creating chat message: {e}")
            return {'statusCode': 500, 'body': 'Error saving message'}

        assistant_response = ""

        # ✅ Safe environment variable lookups with fallback
        STUDENT_PROFILE_API = os.environ.get(
            "STUDENT_PROFILE_API_ENDPOINT",
            "https://8le5se2aja.execute-api.us-west-2.amazonaws.com/Dev/getStudentProfile"
        )
        EDIT_STUDENT_PROFILE_API = os.environ.get(
            "EDIT_STUDENT_PROFILE_API_ENDPOINT",
            "https://8le5se2aja.execute-api.us-west-2.amazonaws.com/Dev/editStudentProfile"
        )

        print(f"Using STUDENT_PROFILE_API: {STUDENT_PROFILE_API}")
        print(f"Using EDIT_STUDENT_PROFILE_API: {EDIT_STUDENT_PROFILE_API}")

        # Fetch student profiles
        studentProfiles = []
        for student in student_ids:
            try:
                studentProfile = post_json(STUDENT_PROFILE_API, {"studentID": student})
                studentProfiles.append(studentProfile)
            except Exception as e:
                print(f"Error fetching student profile for {student}: {e}")
                studentProfiles.append({})

        print(f"Student Profiles: {studentProfiles}")

        # Build system prompt
        system_prompt = ""
        if chat_type == "student":
            print("student chat")
            student_profile_clean = studentProfiles[0].get("body", {}).get("Item", {})
            print(student_profile_clean)
            formatted_profile = format_student_profile(student_profile_clean, teacher_id)
            print(formatted_profile)
            system_prompt = load_prompt_template(
                "prompts/3_7_prompt_student_chat.txt",
                {"STUDENT_PROFILE": formatted_profile}
            )
        elif chat_type == "general":
            print("general chat")
            students_to_disabilties = get_students_data(studentProfiles)
            formatted_mappings = json.dumps(students_to_disabilties, indent=2)
            system_prompt = load_prompt_template(
                "prompts/3_7_prompt_all_chat.txt",
                {"MAPPINGS_JSON": formatted_mappings}
            )
        
        # Conversation history
        try:
            convo_messages = get_chat_messages(teacher_id, session_id)
            formatted_convo = format_history_for_claude(convo_messages)
            formatted_convo.append({
                "role": "user",
                "content": [{"text": body}]
            })
            conversation = formatted_convo
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            conversation = [{
                "role": "user",
                "content": [{"text": body}]
            }]

        # Tool config
        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "editStudentProfile",
                        "description": "Update a student's profile with a teacher's observation or comment.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "teacherComment": { "type": "string" }
                                },
                                "required": ["teacherComment"]
                            }
                        }
                    }
                }
            ]
        }

        # Call Bedrock
        try:
            if chat_type == "general":
                stream_response = bedrock.converse_stream(
                    modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                    messages=conversation,
                    system=[{"text": system_prompt}],
                    inferenceConfig={"maxTokens": 1024, "temperature": 0.3, "topP": 0.9},
                )
            else:
                stream_response = bedrock.converse_stream(
                    modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                    messages=conversation,
                    system=[{"text": system_prompt}],
                    toolConfig=tool_config,
                    inferenceConfig={"maxTokens": 1024, "temperature": 0.3, "topP": 0.9},
                )
        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            return {'statusCode': 500, 'body': 'Error processing request'}

        # Handle streaming response
        stop_reason = ""
        tool_use = {}
        tool_result = None
        tool_was_called = False
        
        for chunk in stream_response["stream"]:
            if "contentBlockDelta" in chunk:
                delta2 = chunk["contentBlockDelta"]["delta"]
                if 'toolUse' in delta2:
                    tool_was_called = True
                    if 'input' not in tool_use:
                        tool_use['input'] = ''
                    tool_use['input'] += delta2['toolUse']['input']
                elif 'text' in delta2:
                    text = chunk["contentBlockDelta"]["delta"]["text"]
                    assistant_response += text
                    try:
                        apigw_client.post_to_connection(
                            ConnectionId=event['requestContext']['connectionId'],
                            Data=json.dumps({'message': text, 'sessionId': session_id, "is_streaming": True}).encode('utf-8')
                        )
                    except Exception as e:
                        print(f"Error sending WebSocket message: {e}")
            elif 'contentBlockStart' in chunk:
                tool = chunk['contentBlockStart']['start']['toolUse']
                tool_use['toolUseId'] = tool['toolUseId']
                tool_use['name'] = tool['name']
            elif 'contentBlockStop' in chunk:
                if 'input' in tool_use:
                    try:
                        tool_use['input'] = json.loads(tool_use['input'])
                    except json.JSONDecodeError as e:
                        print(f"Error parsing tool input JSON: {e}")
                        tool_use['input'] = {}
            elif 'messageStop' in chunk:
                stop_reason = chunk['messageStop']['stopReason']
        
        final_assistant_response = assistant_response

        # Handle tool use
        if stop_reason == "tool_use" and tool_use.get('name') == 'editStudentProfile':
            try:
                tool_result = post_json(
                    EDIT_STUDENT_PROFILE_API,
                    {"studentID": student_ids[0], "teacherID": teacher_id, "teacherComment": body}
                )
            except Exception as e:
                print(f"Error calling editStudentProfile API: {e}")
                tool_result = None

        # Save assistant response
        try:
            create_chat_message(
                user_id=teacher_id,
                conversation_id=session_id,
                message=final_assistant_response,
                sender="assistant"
            )
        except Exception as e:
            print(f"Error saving assistant message: {e}")

        # Title generation
        if not get_conversation_title(teacher_id, session_id):
            try:
                title_prompt = load_prompt_template(
                    "prompts/3_5_prompt_generate_title.txt",
                    {"BODY": body}
                )
                title = call_bedrock(title_prompt)
                update_conversation_title(teacher_id, session_id, title)
            except Exception as e:
                print(f"Error generating title: {e}")

        try:
            apigw_client.post_to_connection(
                ConnectionId=event['requestContext']['connectionId'],
                Data=json.dumps({'sessionId': session_id, 'status': 'complete', 'is_streaming': False}).encode('utf-8')
            )
        except Exception as e:
            print(f"Error sending final WebSocket message: {e}")
        
        return {'statusCode': 200, 'body': json.dumps({'conversationId': session_id, 'status': 'complete'})}
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}
