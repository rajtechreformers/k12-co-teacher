import json
import boto3
import os

def lambda_handler(event, context):
    studentID = event['studentID']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['STUDENT_PROFILES_TABLE'])
    response = table.get_item(Key={'studentID': studentID})
    return {
        'statusCode': 200,
        'body': response
    }
