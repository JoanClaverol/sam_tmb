import boto3
from datetime import datetime

# Initialize the S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    try: 

        bucket_name = event['Records'][0]['s3']['bucket']['name']
        print(f"Bucket name: {bucket_name}")

        print('-----------------')
        print(event)

        # Get the current timestamp
        end_time = datetime.now().isoformat()
        log_content = f"File created!\nEnd time: {end_time}\n"

        # Create a new log file
        log_key = f"logs/log_{end_time}.txt"

        # Write the log content to the file
        s3.put_object(Bucket=bucket_name, Key=log_key, Body=log_content)

        return {
            "statusCode": 200,
            "message": "Log file successfully created",
        }
    except Exception as e:
        print(e)
        raise e