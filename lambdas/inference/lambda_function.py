import json
import boto3
import uuid
from conversation_history import *
from student_utils import *
from utils import *


bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-west-2')

def lambda_handler(event, context):
    if event['requestContext']['routeKey'] == '$connect':
        return {'statusCode': 200}
    
    # Handle disconnect events  
    if event['requestContext']['routeKey'] == '$disconnect':
        return {'statusCode': 200}

    print(f"Event: {event}")
    print(f"Context: {context}")
    
    try:
        # Parse the JSON body
        message_data = json.loads(event.get("body", "{}"))
        body = message_data.get("body") 
        teacher_id = message_data.get("teacherId")
        session_id = message_data.get("sessionId")
        student_ids = message_data.get("studentIDs",[])
        chat_type = "student" if len(student_ids) == 1 else "general"
        class_id = message_data.get("classId", "")

        print(f"Teacher ID: {teacher_id}")
        print(f"Session ID: {session_id}")

        domain = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        api_endpoint = f"https://{domain}/{stage}"

        apigw_client = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=api_endpoint
        )

        if not body or not teacher_id:
            return {'statusCode': 400, 'body': 'Missing body or teacherId'}

        # handling chat history
        is_new_convo = session_id is None
        if is_new_convo:
            session_id = str(uuid.uuid4())
            # create place holder title then change the title.
            try:
                create_conversation(
                    user_id=teacher_id,
                    conversation_attributes={"conversation_id": session_id,"title": "", "type":chat_type, "student_ids":student_ids, "class_id": class_id}
                )
            except Exception as e:
                print(f"Error creating conversation: {e}")
                return {'statusCode': 500, 'body': 'Error creating conversation'}
        
        # user convo msg added to dynamo
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
        conversation = [
                {
                    "role": "user",
                    "content": [{"text": body}],
                }
            ]
        
        # getting student profile from student ids
        studentProfiles = []
        for student in student_ids:
            try:
                student_profile_api_endpoint = os.environ.get('STUDENT_PROFILE_API_ENDPOINT')
                if not student_profile_api_endpoint:
                    raise RuntimeError("STUDENT_PROFILE_API_ENDPOINT environment variable is not set")
                studentProfile = post_json(student_profile_api_endpoint, {"studentID": student})
                studentProfiles.append(studentProfile)
            except Exception as e:
                print(f"Error fetching student profile for {student}: {e}")
                studentProfiles.append({})
        
        print(f"Student Profiles: {studentProfiles}")

        system_prompt = ""
        # conditional claude prompts for student vs. general chat
        if chat_type == "student":
            print("student chat")
            student_profile_clean = studentProfiles[0].get("body", {}).get("Item", {})
            print(student_profile_clean)
            formatted_profile_2 = format_student_profile_2(student_profile_clean, teacher_id)
            print(formatted_profile_2)
            system_prompt = load_prompt_template("prompts/3_7_prompt_student_chat.txt", {
                "STUDENT_PROFILE": formatted_profile_2
            })
            print(system_prompt)
            
        elif chat_type == "general":
            print("general chat")
            # mapping
            students_to_disabilties_2 = get_students_data_2(studentProfiles)
            print(students_to_disabilties_2)
            formatted_mappings = json.dumps(students_to_disabilties_2, indent=2)
            system_prompt = load_prompt_template("prompts/3_7_prompt_all_chat.txt", {
                "MAPPINGS_JSON": formatted_mappings
            })
        
        try:
            convo_messages = get_chat_messages(teacher_id, session_id)
            print(f"convo messages: {convo_messages}")
            formatted_convo = format_history_for_claude(convo_messages)
            print(f"formatted convo: {formatted_convo}")
            formatted_convo.append({
                "role": "user",
                "content": [{"text": body}]
            })
            conversation = formatted_convo
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            # Continue with just the current message

        # tool for EDIT_Q
        tool_config = {
            "tools":[
                {
                    "toolSpec":{
                        "name": "editStudentProfile",
                        "description": "Update a student's profile with a teacher's observation or comment about the given student.",
                        "inputSchema": {
                            "json":{
                                "type": "object",
                                "properties": {
                                    "teacherComment": { "type": "string", "description": "The observation or note about student to be added" }
                                },
                                "required": ["teacherComment"]
                            }
                        }
                    }
                }
            ]
        }           
        
        try:
            if chat_type == "general":
                stream_response = bedrock.converse_stream(
                        modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                        messages=conversation,
                        system = [{"text": system_prompt}],
                        inferenceConfig={"maxTokens": 1024, "temperature": 0.3, "topP": 0.9},
                    )
            elif chat_type == "student":
                stream_response = bedrock.converse_stream(
                        modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                        messages=conversation,
                        system = [{"text": system_prompt}],
                        toolConfig=tool_config,
                        inferenceConfig={"maxTokens": 1024, "temperature": 0.3, "topP": 0.9},
                    )
        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            return {'statusCode': 500, 'body': 'Error processing request'}
        
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
                    print(text, end="")
                    assistant_response += text
                    try:
                        apigw_client.post_to_connection(
                            ConnectionId=event['requestContext']['connectionId'],
                            Data=json.dumps({'message': text, 'sessionId':session_id, "is_streaming":True}).encode('utf-8')
                        )
                    except Exception as e:
                        print(f"Error sending WebSocket message: {e}")
                        # Continue processing even if WebSocket fails
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
        
        if stop_reason == "tool_use" and tool_use.get('name') == 'editStudentProfile':
            try:
                editStudentProfileApiEndpoint = os.environ.get('EDIT_STUDENT_PROFILE_API_ENDPOINT')
                if not editStudentProfileApiEndpoint:
                    raise RuntimeError("EDIT_STUDENT_PROFILE_API_ENDPOINT environment variable is not set")
                tool_result = post_json(editStudentProfileApiEndpoint, 
                                {"studentID": student_ids[0],
                                "teacherID": teacher_id,
                                "teacherComment": body})
            except Exception as e:
                print(f"Error calling editStudentProfile API: {e}")
                tool_result = None

            if tool_result:
                try:
                    # Update conversation with tool result for second call
                    updated_conversation = conversation.copy()
                    updated_conversation.append({
                        "role": "assistant",
                        "content": [{"text": assistant_response}]
                    })
                    updated_conversation.append({
                        "role": "user", 
                        "content": [{"text": json.dumps(tool_result)}]
                    })
                    
                    stream_response = bedrock.converse_stream(
                        modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                        messages=updated_conversation,
                        system = [{"text": system_prompt}],
                        inferenceConfig={"maxTokens": 1024, "temperature": 0.3, "topP": 0.9},
                    )
                    assistant_response2 = ""
                    for chunk in stream_response["stream"]:
                        if "contentBlockDelta" in chunk:
                            delta2 = chunk["contentBlockDelta"]["delta"]
                            if 'text' in delta2:
                                text = chunk["contentBlockDelta"]["delta"]["text"]
                                print(text, end="")
                                assistant_response2 += text
                                try:
                                    apigw_client.post_to_connection(
                                        ConnectionId=event['requestContext']['connectionId'],
                                        Data=json.dumps({'message': text, 'sessionId':session_id, "is_streaming":True}).encode('utf-8')
                                    )
                                except Exception as e:
                                    print(f"Error sending WebSocket message: {e}")
                    
                    # Use the second response as the final response to store
                    final_assistant_response = assistant_response2
                except Exception as e:
                    print(f"Error handling tool result: {e}")
        
        # Always store exactly one assistant response per user message
        try:
            create_chat_message(
                user_id=teacher_id,
                conversation_id=session_id,
                message=final_assistant_response,
                sender="assistant"
            )
        except Exception as e:
            print(f"Error saving assistant message: {e}")

        # Generate title
        if not get_conversation_title(teacher_id, session_id):
            try:
                title_prompt = load_prompt_template("prompts/3_5_prompt_generate_title.txt", {
                        "BODY": body
                    })
                title = call_bedrock(title_prompt)
                print(f"Title: {title}")
                update_conversation_title(teacher_id, session_id, title)
            except Exception as e:
                print(f"Error generating title: {e}")

        try:
            apigw_client.post_to_connection(
                ConnectionId=event['requestContext']['connectionId'],
                Data=json.dumps({
                    'sessionId': session_id,
                    'status': 'complete',
                    'is_streaming': False
                }).encode('utf-8')
            )
        except Exception as e:
            print(f"Error sending final WebSocket message: {e}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'conversationId': session_id, 'status': 'complete'})
        }
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }