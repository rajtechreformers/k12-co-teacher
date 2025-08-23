import json
import boto3

def lambda_handler(event, context):
    studentID = event['studentID']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('k12-coteacher-student-profiles')
    response = table.get_item(Key={'studentID': studentID})
    return {
        'statusCode': 200,
        'body': response
    }
