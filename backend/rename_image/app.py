# rename_images/
import os
import json
import uuid
import boto3
import urllib.parse
from botocore.exceptions import ClientError

IMAGE_TABLE = os.environ['IMAGE_TABLE']
IMAGE_BUCKET = os.environ['IMAGE_BUCKET']
INCOMING_BUCKET = os.environ['INCOMING_BUCKET']

s3 = boto3.client('s3')

def decode_object_name(object_name):
    # Decode the object name from the URL-encoded format
    return urllib.parse.unquote_plus(object_name)

def rename_object(bucket, key):
    
    new_key = str(uuid.uuid4())
    try:
        s3.copy_object(Bucket=IMAGE_BUCKET, CopySource={'Bucket': bucket, 'Key': key}, Key=new_key)
    except ClientError as e:
        print(e)
        return False
    else:
        print('New key: ' + new_key)
        print('Old key: ' + key)
        print('Bucket: ' + bucket)
        print('Table: ' + IMAGE_TABLE)
        print('Image bucket: ' + IMAGE_BUCKET)
        print('Incoming bucket: ' + INCOMING_BUCKET)
        return new_key
    

def lambda_handler(event, context):

    print(event)
    object_name = decode_object_name(event['Records'][0]['s3']['object']['key'])

    rename_status = rename_object(INCOMING_BUCKET, object_name)
    if rename_status:
        print('Successfully renamed object:', str(rename_status))
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully renamed object')
    }
