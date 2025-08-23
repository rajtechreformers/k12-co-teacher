import json
import boto3

def lambda_handler(event, context):
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table('k12-coteacher-student-profiles')
    studentID = event['studentID']
    teacherID = event['teacherID']
    comment = event['teacherComment']

    # add teacher comments to sutudent profile
    try:

        response = table.get_item(Key={'studentID': studentID})
        item = response.get('Item', {})
        comments = item.get('teacherComments', {})

        if teacherID in comments:
            comments[teacherID].append(comment)
        else:
            comments[teacherID] = [comment]

        table.update_item(
            Key={'studentID': studentID},
            UpdateExpression='SET teacherComments = :updated',
            ExpressionAttributeValues={
                ':updated': comments
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps(f"Comment added for teacher {teacherID}.")
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error updating comment: {str(e)}")
        }