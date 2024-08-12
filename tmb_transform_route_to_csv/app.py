import json
from utils import extract_routes
import boto3

# Initialize the S3 client
s3 = boto3.client('s3')


def lambda_handler(event, context):
    """
    Lambda handler function to transform a JSON file containing journey plans into a CSV file with route information.

    Parameters:
    - event: The event data passed to the Lambda function.
    - context: The runtime information of the Lambda function.

    Returns:
    - A dictionary containing the status code and message indicating the success of the transformation
    """

    try: 

        # get bucket and key from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        # get the file from s3
        file = s3.get_object(Bucket=bucket, Key=key)
        file_content = file['Body'].read().decode('utf-8')
        data = json.loads(file_content)
        csv = extract_routes(data)

        # replace the key extension to remove the folder path and only get the file name, and remove the extension
        folder_name = key.split('/')[0]
        key = key.replace(f'{folder_name}/', '').replace('.json', '')

        # store the file on route_csv/ in the same bucket
        try: 
            s3.put_object(Bucket=bucket, Key=f'routes_csv/{key}.csv', Body=csv.to_csv(index=False))
            print(f"CSV file successfully created on route_csv/ in {bucket} on S3 {key}.csv")
        except Exception as e:
            print(e)
            raise e

        return {
            "statusCode": 200,
            "message": "CSV file successfully created on route_csv/ and root directory",
        }
    except Exception as e:
        print(e)
        raise e
