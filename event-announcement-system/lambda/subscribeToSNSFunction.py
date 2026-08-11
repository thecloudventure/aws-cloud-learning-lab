import json
import boto3


def lambda_handler(event, context):
    # Log the complete request so it can be inspected in CloudWatch
    # during testing and troubleshooting.
    print("Event received:", json.dumps(event))

    # API Gateway places the incoming request data inside the "body" field.
    if 'body' in event:

        # The body can arrive either as a dictionary or as a JSON string,
        # depending on how API Gateway is configured.
        if isinstance(event['body'], dict):
            body = event['body']
        else:
            body = json.loads(event['body'])

        # Extract the subscriber's email address from the request.
        email = body.get('email', None)

        if email:
            # Create an SNS client that Lambda will use to manage
            # subscriptions for the EventAnnouncements topic.
            sns_client = boto3.client('sns')

            try:
                # Create an email subscription for the provided address.
                #
                # IMPORTANT:
                # SNS sends a confirmation email to this address.
                # The subscription remains "PendingConfirmation" until
                # the recipient clicks the confirmation link.
                response = sns_client.subscribe(
                    TopicArn='enter-sns-topic-ARN',
                    Protocol='email',
                    Endpoint=email
                )

                # Log the SNS response so we can see the subscription ARN
                # and verify that SNS accepted the subscription request.
                print("SNS subscription response:", response)

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': (
                            'Subscription successful! '
                            'Please check your email to confirm.'
                        )
                    })
                }

            except Exception as e:
                # Log the error in CloudWatch for troubleshooting.
                print(f"Error subscribing user: {str(e)}")

                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': f'Failed to subscribe: {str(e)}'
                    })
                }

        else:
            # Return a bad request response when the email address
            # is missing from the request.
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Email not provided.'
                })
            }

    # Return a bad request response when the request does not contain
    # the structure expected by the Lambda function.
    return {
        'statusCode': 400,
        'body': json.dumps({
            'error': 'Invalid request format.'
        })
    }