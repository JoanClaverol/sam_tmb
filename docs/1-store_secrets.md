Certainly! Let's set up your AWS SAM project so that you can deploy it using the `sam deploy --guided` step and automatically load environment variables from your `.env` file.

### Step 1: Ensure Your `.env` File is Correct

Your `.env` file should be in the root directory of your SAM project and should look like this:

```plaintext
TMB_APP_ID= # your id here
TMB_APP_KEY= # your api key here
```

### Step 2: Update Your `template.yaml`

Update your `template.yaml` to use the AWS Secrets Manager for storing your secrets:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: |
  tmb-api
  Sample SAM Template for tmb-api

Globals:
  Function:
    Timeout: 15
    MemorySize: 128

Resources:
  TMBBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: tmbinfo

  TMBSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: TMBApiSecrets
      Description: "Secrets for TMB API"
      SecretString: !Sub |
        {
          "TMB_APP_ID": "${TMB_APP_ID}",
          "TMB_APP_KEY": "${TMB_APP_KEY}"
        }

  TMBGetRoute:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: tmb_get_route/
      Handler: app.lambda_handler
      Runtime: python3.9
      Architectures:
        - x86_64
      Environment:
        Variables:
          BucketName: !Ref TMBBucket
          SecretName: !Ref TMBSecret
      Policies:
        - Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - s3:PutObject
              Resource: arn:aws:s3:::tmbinfo/*
            - Effect: Allow
              Action:
                - secretsmanager:GetSecretValue
              Resource: !Sub arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:TMBApiSecrets

  TMBGetRouteUrl:
    Type: AWS::Lambda::Url
    Properties:
      AuthType: NONE
      TargetFunctionArn: !GetAtt TMBGetRoute.Arn

  TMBGetRouteUrlPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunctionUrl
      FunctionName: !Ref TMBGetRoute
      Principal: "*"
      FunctionUrlAuthType: NONE

Outputs:
  TMBBucket:
    Description: TMB Bucket
    Value: !Ref TMBBucket
  TMBGetRoute:
    Description: TMB Get Route
    Value: !GetAtt TMBGetRoute.Arn
  TMBGetRouteUrl:
    Description: TMB Get Route URL
    Value: !GetAtt TMBGetRouteUrl.FunctionUrl
```

### Step 3: Load Environment Variables from the `.env` File

Use a tool to load environment variables from your `.env` file before running `sam deploy --guided`. Here’s how you can do it using `dotenv-cli`:

1. **Install `dotenv-cli`** if you haven't already:

   ```sh
   npm install -g dotenv-cli
   ```

2. **Deploy using `dotenv-cli`** to load the environment variables:

   ```sh
   dotenv -e .env -- sam deploy --guided
   ```

### Step 4: Follow the `sam deploy --guided` Steps

When you run the above command, follow the prompts to complete the deployment. During the deployment process, the environment variables from your `.env` file will be used to populate the values in AWS Secrets Manager.

### Step 5: Update Your Lambda Function to Retrieve Secrets

Ensure your Lambda function is updated to retrieve secrets from AWS Secrets Manager:

```python
import os
from datetime import datetime
import requests
import boto3
import json

# Configuration
BASE_URL = "https://api.tmb.cat/v1/"
ENDPOINT = "planner/plan"
BUCKET = os.environ['BucketName']
BUCKET_FOLDER = "routes_from_api"

def get_secret():
    secret_name = os.environ['SecretName']
    region_name = os.environ['AWS_REGION']

    client = boto3.client('secretsmanager', region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(get_secret_value_response['SecretString'])
    return secret

def get_journey_plan(home_location, work_location, tmb_app_id, tmb_app_key):
    from_place = f"{home_location['latitude']},{home_location['longitude']}"
    to_place = f"{work_location['latitude']},{work_location['longitude']}"
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M")
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
    try:
        secret = get_secret()
        tmb_app_id = secret['TMB_APP_ID']
        tmb_app_key = secret['TMB_APP_KEY']
        home_location = {
            'latitude': 41.423043,
            'longitude': 2.184006
        }
        work_location = {
            'latitude': 41.406232,
            'longitude': 2.192273
        }

        journey_plan = get_journey_plan(home_location, work_location, tmb_app_id, tmb_app_key)
        store_journey_plan(journey_plan)

        return {
            "statusCode": 200,
            "message": "Journey plan successfully retrieved",
            "body": journey_plan,
        }

    except requests.RequestException as e:
        print(e)
        raise e
```

By following these steps, your Lambda function will securely retrieve the `TMB_APP_ID` and `TMB_APP_KEY` from AWS Secrets Manager. This approach ensures that sensitive information is not hardcoded into your Lambda function or SAM template.
