## get_images/

import os
import json
import uuid
import boto3
import urllib.parse
from botocore.exceptions import ClientError

if os.environ.get('AWS_SAM_LOCAL'):
    os.environ['IMAGE_TABLE'] = 'dbla-ml-photo-album-image-table'

IMAGE_TABLE = os.environ['IMAGE_TABLE']
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):

    print(IMAGE_TABLE)
    # Provide json list of images from dyanmoDB
    table = dynamodb.Table(IMAGE_TABLE)
    try:
        response = table.scan()
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:

        items = response['Items']
        return {
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }

if __name__ == "__main__":
    
    lambda_handler(None, None)