import boto3, uuid, os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

dynamo = boto3.resource('dynamodb')
table = dynamo.Table(os.environ['CHAT_HISTORY_TABLE'])

# conversation history
def create_conversation(user_id, conversation_attributes):
    created_at = int(datetime.utcnow().timestamp())
    conversation_id = conversation_attributes['conversation_id']
    item = {
        'TeacherId': user_id,
        'sortId': f'CONV#{conversation_id}',
        'created_at': created_at,
        'conversation_id': conversation_id,
        'title': conversation_attributes['title'],
        'type': conversation_attributes.get('type', 'general'),
        'student_ids': conversation_attributes.get('student_ids', []),
        'class_id': conversation_attributes.get('class_id', ''),
    }
    table.put_item(Item=item)
    return item

def create_chat_message(user_id, conversation_id, message, sender):
    # Generate a ULID for the message
    # message_ulid = str(ulid.new())
    # changing this for now..
    message_ulid = str(uuid.uuid4())
   
    created_at = int(datetime.utcnow().timestamp())
    expires_at = int((datetime.utcnow() + timedelta(days=90)).timestamp())
   
    item = {
        'TeacherId': user_id,
        'sortId': f'CHAT#{conversation_id}#MSG#{message_ulid}',
        'created_at': created_at,
        'message': message,
        'sender': sender,
    }
   
    table.put_item(Item=item)
    return item

def update_conversation_title(user_id, conversation_id, new_title):
    response = table.update_item(
        Key={
            'TeacherId': user_id,
            'sortId': f'CONV#{conversation_id}'
        },
        UpdateExpression='SET #t = :new_title',
        ExpressionAttributeNames={
            '#t': 'title'
        },
        ExpressionAttributeValues={
            ':new_title': new_title
        },
        ReturnValues='UPDATED_NEW'
    )
    return response

def get_chat_messages(user_id, conversation_id):
    sort_key_prefix = f'CHAT#{conversation_id}#MSG'
   
    response = table.query(
        KeyConditionExpression=Key('TeacherId').eq(user_id) & Key('sortId').begins_with(sort_key_prefix)
    )
    items = response.get('Items', [])
    return items

def get_conversation_title(user_id, conversation_id):
    try:
        response = table.get_item(
            Key={
                'TeacherId': user_id,
                'sortId': f'CONV#{conversation_id}'
            }
        )
        item = response.get('Item', {})
        return item.get('title', '')
    except Exception as e:
        print(f"Error getting conversation title: {e}")
        return ''

def delete_conversation(user_id, conversation_id):
    # Get all message items related to the conversation
    message_items = get_chat_messages(user_id, conversation_id)
   
    with table.batch_writer() as batch:
        # Delete the metadata item
        batch.delete_item(
            Key={
                'TeacherId': user_id,
                'sortId': f'CONV#{conversation_id}'
            }
        )
        # Delete all message items
        for item in message_items:
            batch.delete_item(
                Key={
                    'TeacherId': item['TeacherId'],
                    'sortId': item['sortId']
                }
            )
