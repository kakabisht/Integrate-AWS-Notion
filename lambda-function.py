import boto3
import json
import os
import requests

cloudwatch_logs = boto3.client('logs')
cloudtrail = boto3.client('cloudtrail')

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_API_KEY = os.environ['NOTION_API_KEY']
NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']

def lambda_handler(event, context):
    # Extract log group and log stream name from the event
    log_group_name = event['awslogs']['logGroup']
    log_stream_name = event['awslogs']['logStream']
    
    # Get CloudWatch log events
    log_events = get_cloudwatch_log_events(log_group_name, log_stream_name)
    
    # Get CloudTrail events
    cloudtrail_events = get_cloudtrail_events()
    
    # Push logs to Notion
    push_logs_to_notion(log_events, cloudtrail_events)

    return {
        'statusCode': 200,
        'body': json.dumps('Logs processed successfully')
    }

def get_cloudwatch_log_events(log_group_name, log_stream_name):
    response = cloudwatch_logs.get_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        startFromHead=True
    )
    return response['events']

def get_cloudtrail_events():
    response = cloudtrail.lookup_events(
        LookupAttributes=[
            {
                'AttributeKey': 'EventName',
                'AttributeValue': 'RunInstances'
            }
        ],
        MaxResults=10
    )
    return response['Events']

def push_logs_to_notion(cloudwatch_logs, cloudtrail_logs):
    for log in cloudwatch_logs:
        create_notion_page(f"CloudWatch Log: {log['message']}")
    
    for event in cloudtrail_logs:
        create_notion_page(f"CloudTrail Event: {event['EventName']} - {event['EventId']}")

def create_notion_page(content):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(NOTION_API_URL, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        print(f"Failed to create Notion page: {response.status_code}, {response.text}")

# Example event structure to test locally
if __name__ == "__main__":
    event = {
        'awslogs': {
            'logGroup': 'your-log-group',
            'logStream': 'your-log-stream'
        }
    }
    context = {}
    lambda_handler(event, context)
