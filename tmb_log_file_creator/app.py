import boto3
from datetime import datetime

# Initialize the S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_created = event['Records'][0]['s3']['object']['key']
        event_time = event['Records'][0]['eventTime']
        log_key = "logs/logs.txt"
        temp_log_key = "logs/logs_temp.txt"

        # Initialize log_content
        log_content = ""

        # Try to fetch the existing log file from S3
        try:
            current_log = s3.get_object(Bucket=bucket_name, Key=log_key)
            log_content = current_log['Body'].read().decode('utf-8')
        except s3.exceptions.NoSuchKey:
            # If the log file does not exist, log_content remains empty
            print(f"{log_key} does not exist. Creating a new log file.")

        # Split the log content into individual entries
        log_entries = log_content.splitlines()

        # Get the current timestamp
        end_time = datetime.now().isoformat()
        new_log_entry = f"New file created: {file_created} at {event_time}. Log entry added at {end_time}"

        # Add the new log entry
        log_entries.append(new_log_entry)

        # Check if there are more than 100 entries
        if len(log_entries) > 100:
            # Remove the oldest entry (first in the list)
            log_entries.pop(0)

        # Join the entries back into a single string
        updated_log_content = "\n".join(log_entries) + "\n"

        # Upload the updated log content to the temporary log file
        s3.put_object(Bucket=bucket_name, Key=temp_log_key, Body=updated_log_content.encode('utf-8'))

        # If the upload was successful, rename the temporary log file to the actual log file
        s3.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': temp_log_key}, Key=log_key)

        # Delete the temporary log file
        s3.delete_object(Bucket=bucket_name, Key=temp_log_key)

        return {
            "statusCode": 200,
            "message": "Log file successfully updated",
        }
    except Exception as e:
        print(e)
        raise e