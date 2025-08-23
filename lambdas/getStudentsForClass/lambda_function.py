import json
import boto3

def lambda_handler(event, context):
    classID = event['classID']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('k12-coteacher-class-to-students')
    students = table.get_item(Key={'classID': classID})['Item']['students']
    return {
        'statusCode': 200,
        'body': students
    }
