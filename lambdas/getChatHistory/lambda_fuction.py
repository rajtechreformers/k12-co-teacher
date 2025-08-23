import json
import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    # config
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table('k12-coteacher-chat-history')
    teacher_id = event['teacherId']
    conversation_id = event.get('conversationId')
    class_id = event.get('classId')

    # flow 1: teacher ID, convoId -> list of messages
    if conversation_id:
        sort_key_prefix = f'CHAT#{conversation_id}#MSG'
        response = table.query(
            KeyConditionExpression=Key('TeacherId').eq(teacher_id) & Key('sortId').begins_with(sort_key_prefix),
            ScanIndexForward=True # oldest to newest
        )
        items = response.get('Items', [])
        return items
    
    # flow 2 : teacherID -> all of the teacher's convos
    else:
        response = table.query(
            KeyConditionExpression=Key('TeacherId').eq(teacher_id) &
                                   Key('sortId').begins_with('CONV#'),
            FilterExpression='class_id = :class_id',
            ExpressionAttributeValues={':class_id': class_id},
            ScanIndexForward=True # oldest to newest
        )
        items = response.get('Items', [])
        return items
