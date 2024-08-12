import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import boto3
from botocore.exceptions import ClientError
import json

load_dotenv()

# Configuration
BASE_URL = "https://api.tmb.cat/v1/"
ENDPOINT = "planner/plan"
BUCKET = "tmbinfo"
BUCKET_FOLDER = "routes_from_api"
HOME_LOCATION = {
    'latitude': 41.423043,
    'longitude': 2.184006
}

WORK_LOCATION = {
    'latitude': 41.406232,
    'longitude': 2.192273
}

# get secrets
def get_secret():

    secret_name = "tmb-secrets"
    region_name = "eu-west-3"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

secrets = get_secret()
TMB_APP_ID = secrets['TMB_APP_ID']
TMB_APP_KEY = secrets['TMB_APP_KEY']

def get_journey_plan(home_location, work_location, tmb_app_id, tmb_app_key):
    """
    Retrieve the journey plan from TMB API.

    Parameters:
        home_location (dict): The starting location with 'latitude' and 'longitude'.
        work_location (dict): The destination location with 'latitude' and 'longitude'.
        tmb_app_id (str): TMB API application ID.
        tmb_app_key (str): TMB API application key.

    Returns:
        dict: Journey plan data from the API response.
    """
    from_place = f"{home_location['latitude']},{home_location['longitude']}"
    to_place = f"{work_location['latitude']},{work_location['longitude']}"
    date = datetime.now().strftime("%m-%d-%Y")  
    time = datetime.now().strftime("%I:%M%p").lower() 
    mode = ['TRANSIT', 'WALK']

    params = {
        'app_key': tmb_app_key,
        'app_id': tmb_app_id,
        'fromPlace': from_place,
        'toPlace': to_place,
        'date': date,
        'time': time,
        'mode': ','.join(mode),
        'showIntermediateStops': True
    }

    response = requests.get(f"{BASE_URL}{ENDPOINT}", params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def store_journey_plan(journey_plan):
    """
    Store the journey plan in an S3 bucket, in the folder routes_from_api.

    Parameters:
        journey_plan (dict): The journey plan data to store.
    """
    try: 
        s3 = boto3.client('s3')
        key = f"{BUCKET_FOLDER}/journey_plan_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
        journey_plan_json = json.dumps(journey_plan)
        s3.put_object(Bucket=BUCKET, Key=key, Body=journey_plan_json.encode('utf-8'))

        return {
            "statusCode": 200,
            "message": "Journey plan successfully stored",
        }
    except Exception as e:
        print(e)
        raise e

def lambda_handler(event, context):
    """
    Lambda function handler for retrieving and storing journey plans.

    Parameters:
        event (dict): Event data passed by Lambda.
        context (object): Context object provided by Lambda.

    Returns:
        dict: API Gateway Lambda Proxy Output Format.
    """
    try:
        
        journey_plan = get_journey_plan(HOME_LOCATION, WORK_LOCATION, TMB_APP_ID, TMB_APP_KEY)
        store_journey_plan(journey_plan)

        return {
            "statusCode": 200,
            "message": "Journey plan successfully retrieved",
            "body": journey_plan,
        }
    
    except requests.RequestException as e:
        print(e)
        raise e