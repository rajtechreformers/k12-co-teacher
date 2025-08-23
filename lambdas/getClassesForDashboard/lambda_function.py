import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
classes_for_teacher_table = dynamodb.Table('k12-coteacher-teachers-to-classes')
class_attributes_table = dynamodb.Table('k12-coteacher-class-attributes')

def lambda_handler(event, context):
    try:
        print(event)
        teacher_id = event['teacherID']
        
        # Get class IDs for the teacher
        response = classes_for_teacher_table.get_item(Key={'teacherID': teacher_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Teacher not found'})
            }
        
        class_ids = response['Item']['classes']
        
        # Get attributes for each class
        classes_data = []
        for class_id in class_ids:
            class_response = class_attributes_table.get_item(Key={'classID': class_id})
            if 'Item' in class_response:
                classes_data.append(class_response['Item'])
        
        return {
            'statusCode': 200,
            'body': json.dumps(classes_data)
        }
        
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'teacherID is required'})
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Database error: {str(e)}'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
