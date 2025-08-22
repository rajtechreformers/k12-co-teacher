import boto3
import json
import os
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('k12-coteacher-class-to-students') 

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def load_and_add_student(file_path):
    with open(file_path, 'r') as f:
        student_data = json.load(f, parse_float=Decimal)

    # Add to DynamoDB
    table.put_item(Item=student_data)

# Find all JSON files in the directory
directory = 'sample-class-to-student/hist-hs'
student_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.json')]

for file_path in student_files:
    try:
        load_and_add_student(file_path)
    except Exception as e:
        print(f"Error adding {file_path}: {str(e)}")

print("All student profiles added to DynamoDB table")