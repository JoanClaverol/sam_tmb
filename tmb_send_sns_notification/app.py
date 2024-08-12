import json
import boto3
import os
import pandas as pd

sns_client = boto3.client('sns')
sns_topic_arn = os.environ['SNSTopicArn']

def process_time_data(df):
    """
    Transform timestamps to datetime, calculate total time, and determine the ID with the least time difference.

    Parameters:
    df (pandas.DataFrame): DataFrame containing the columns 'start_time', 'end_time', 'id', and 'mode'.

    Returns:
    tuple: (id with the least time difference, concatenated string of unique modes for that ID)
    """
    # Convert epoch timestamps to datetime
    df['start_time'] = pd.to_datetime(df['start_time'], unit='ms')
    df['end_time'] = pd.to_datetime(df['end_time'], unit='ms')

    # Calculate the total time for each row
    df['total_time'] = (df['end_time'] - df['start_time']).dt.total_seconds()

    # Group by 'id' and calculate min start_time, max end_time, and total time
    df_min_max_time = df.groupby('id').agg({
        'start_time': 'min',
        'end_time': 'max',
        'total_time': 'sum'
    }).reset_index()

    # Calculate the difference in time between min start_time and max end_time
    df_min_max_time['diff_time'] = df_min_max_time['end_time'] - df_min_max_time['start_time']

    # Find the id with the least time difference
    id_less_diff_time = df_min_max_time.loc[df_min_max_time['diff_time'].idxmin(), 'id']

    # Filter the rows corresponding to the ID with the least time difference
    df_id_less_diff_time = df[df['id'] == id_less_diff_time]

    # Get the unique modes for that ID and concatenate them into a single string
    unique_modes = df_id_less_diff_time['mode'].unique()
    way_to_go = ' & '.join(unique_modes.tolist())

    return way_to_go

def lambda_handler(event, context):

    # get the bucket name and key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # read the CSV file from S3
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=key)
    df = pd.read_csv(obj['Body'])

    # Process the time data
    way_to_go = process_time_data(df)

    # After successful processing, publish an SNS notification
    sns_client.publish(
        TopicArn=sns_topic_arn,
        Message=f"The best way to go today is {way_to_go}",
        Subject="Update on today's route"
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Route transformed and notification sent successfully!')
    }