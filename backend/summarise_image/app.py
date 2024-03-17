# summarise_image/
import os
import json
import boto3
import base64
import urllib.parse
from botocore.exceptions import ClientError

IMAGE_TABLE = os.environ['IMAGE_TABLE']
IMAGE_BUCKET = os.environ['IMAGE_BUCKET']

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')

def extract_substring(text, trigger_str, end_str):
    # Find string between two values (Thanks for this Mike!)
    last_trigger_index = text.rfind(trigger_str)
    if last_trigger_index == -1:
        return ""
    next_end_index = text.find(end_str, last_trigger_index)
    if next_end_index == -1:
        return ""
    substring = text[last_trigger_index + len(trigger_str):next_end_index]
    return substring

def decode_object_name(object_name):
    # Decode the object name from the URL-encoded format
    return urllib.parse.unquote_plus(object_name)

# Function to get the image and turn it into a base64 string
def get_image_base64(bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        print(e)
        return False
    else:
        image = response['Body'].read()
        return image

def get_image_type(bucket, key):
    # Get the Mime type using object key and head_object
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        print(e)
        return False
    else:
        content_type = response['ContentType']
        print(content_type)
        return content_type

def generate_summary(image_base64, content_type):
    # Generate a summary of the input image using the Bedrock Runtime and claude3 model 

    prompt = """Your purpose is to catalog images based upon common categories. 
Create a structured set of data in json providing a summary of the image and a very short, generalised, image category.  Do not return any narrative language.
Before you provide any output, show your working in <scratchpad> XML tags.
JSON fields must be labelled image_summary and image_category. 

Example json structure is:

<json>
{
    "image_summary": SUMMARY OF THE IMAGE,
    "image_category": SHORT CATEGORY OF THE IMAGE,
}
</json>

Examples of categorie are:

Animals
Nature
People
Travel
Food
Technology
Business
Education
Health
Sports
Arts
Fashion
Backgrounds
Concepts
Holidays
    
Output the json structure as a stringin <json> XML tags.  Do not return any narrative language.

Look at the images in detail, looking for people, animals, landmarks or features and where possible try to identify them.
"""
    
    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image", 
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": image_base64
                            }
                        },
                        # {
                        #     "type": "text",
                        #     "text": prompt
                        # }
                    ]
                }
            ]
        })
    )

    print(response)
    return json.loads(response.get('body').read())

def store_summary(object_id, summary, category):
    # Store the summary in DynamoDB
    
    table = dynamodb.Table(IMAGE_TABLE)
    table.put_item(
        Item={
            'id': object_id,
            'summary': summary,
            'category': category
        }
    )

def lambda_handler(event, context):

    print(json.dumps(event, indent=4))
    object_name = decode_object_name(event['Records'][0]['s3']['object']['key'])

    image_type = get_image_type(IMAGE_BUCKET, object_name)
    image_base64 = get_image_base64(IMAGE_BUCKET, object_name)

    if not image_base64:
        return {
            'statusCode': 500,
            'body': json.dumps('Error getting image')
        }
    else:
        image_base64 = base64.b64encode(image_base64).decode('utf-8')
        response_body = generate_summary(image_base64, image_type)
        
        print(response_body)
        
        summary = response_body['content'][0]['text']
        json_summary = json.loads(extract_substring(summary, "<json>", "</json>"))
        
        image_summary = json_summary['image_summary']
        image_category = json_summary['image_category']
        store_summary(object_name, image_summary, image_category)

    return {
        'statusCode': 200,
        'body': json.dumps('Summary stored in DynamoDB')
    }
