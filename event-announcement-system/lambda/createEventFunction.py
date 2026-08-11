import json
import boto3
from botocore.exceptions import ClientError


# Create the AWS service clients outside the Lambda handler.
# These clients can be reused when AWS reuses a warm Lambda execution environment,
# reducing the need to create new clients for every invocation.
s3 = boto3.client('s3')
sns = boto3.client('sns')


# S3 bucket containing the events.json file.
bucket_name = 'your-bucket-name'

# Name of the JSON file that stores all event information.
events_file_key = 'events.json'

# SNS topic used to notify confirmed subscribers about new events.
sns_topic_arn = 'your-sns-topic-arn'


def lambda_handler(event, context):

    try:
        # API Gateway provides the request body through event['body'].
        # Because the body is received as a JSON string, convert it into
        # a Python dictionary so we can access the event fields.
        new_event = json.loads(event['body'])

        # Retrieve the existing events.json file from S3.
        response = s3.get_object(
            Bucket=bucket_name,
            Key=events_file_key
        )

        # Read the file contents and convert the JSON data into
        # a Python list of events.
        events_data = json.loads(
            response['Body'].read().decode('utf-8')
        )

        # Add the newly submitted event to the existing list.
        events_data.append(new_event)

        # Write the updated list of events back to events.json.
        # This replaces the previous version of the file with the
        # newly updated event list.
        s3.put_object(
            Bucket=bucket_name,
            Key=events_file_key,
            Body=json.dumps(events_data, indent=2),
            ContentType='application/json'
        )

        # Create the notification message that will be sent
        # to confirmed SNS email subscribers.
        message = (
            f"New Event: {new_event['title']} "
            f"on {new_event['date']}\n"
            f"{new_event['description']}"
        )

        # Publish the new event announcement to the SNS topic.
        # SNS then distributes the message to all confirmed subscribers.
        sns.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject="New Event Announcement"
        )

        # Return a successful response to API Gateway.
        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps({
                'message': 'Event created successfully!'
            })
        }

    except ClientError as e:
        # Handle AWS service errors, such as S3 access problems
        # or SNS permission issues.
        print(f"AWS Service Error: {e}")

        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps({
                'message': 'Error processing the event'
            })
        }

    except Exception as e:
        # Handle unexpected errors that are not specifically
        # related to an AWS service call.
        print(f"Unexpected Error: {e}")

        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps({
                'message': 'Unexpected error occurred'
            })
        }