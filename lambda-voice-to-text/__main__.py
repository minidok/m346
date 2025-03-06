import pulumi
import pulumi_aws as aws

# Create an IAM role for the Lambda function
lambda_role = aws.iam.Role("lambdaRole",
    assume_role_policy="""
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
""")

# Attach the necessary policies to the role
policy_lambda_execution = aws.iam.RolePolicyAttachment("lambdaExecutionPolicy",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")

policy_transcribe_access = aws.iam.RolePolicyAttachment("transcribeAccessPolicy",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonTranscribeFullAccess")

# Define the Lambda function
lambda_function = aws.lambda_.Function("voiceToTextFunction",
    role=lambda_role.arn,
    runtime="python3.9",
    handler="voice_to_text.handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./voice_to_text_lambda"),
    }),
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "AWS_REGION": aws.config.region,
        }
    ),
    timeout=300)

# Example Lambda handler
with open("voice_to_text_lambda/voice_to_text.py", "w") as f:
    f.write("""\
import boto3

def handler(event, context):
    transcribe_client = boto3.client('transcribe')
    job_name = event['job_name']
    job_uri = event['job_uri']
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='mp3',
        LanguageCode='en-US'
    )
    return response
""")

# Export the Lambda function ARN
pulumi.export("lambda_function_arn", lambda_function.arn)