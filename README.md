# TMB API Project

This project is an AWS Lambda function that retrieves journey plans from the TMB API and stores them in an S3 bucket. The function can be accessed via a public URL.

## Project Structure

```
tmb-api-project/
├── template.yaml
└── tmb_get_route/
    └── app.py
```

## Prerequisites

- AWS CLI configured with appropriate permissions.
- AWS SAM CLI installed. Follow the instructions [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
- Python 3.9 installed.

## Setup Instructions

### Step 1: Set Up Your Python Project

1. **Create a Project Directory**:

   ```sh
   mkdir tmb-api-project
   cd tmb-api-project
   ```

2. **Create a Virtual Environment**:

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Necessary Packages**:

   ```sh
   pip install boto3 requests
   ```

4. **Create a Directory for Lambda Function Code**:

   ```sh
   mkdir tmb_get_route
   ```

5. **Create the Lambda Function Code**:
   Create a file named `app.py` inside the `tmb_get_route` directory with the following content:

   ```python
   import json
   import os
   from datetime import datetime
   import requests
   import boto3

   # Configuration
   BASE_URL = "https://api.tmb.cat/v1/"
   ENDPOINT = "planner/plan"
   BUCKET = "tmbinfo"
   BUCKET_FOLDER = "routes_from_api"

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
           tmb_app_id = os.getenv('TMB_APP_ID')
           tmb_app_key = os.getenv('TMB_APP_KEY')

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

### Step 2: Create a Simple Lambda Function

1. **Create the `template.yaml`**:
   Create a file named `template.yaml` in the root of your project directory with the following content:

   ```yaml
   AWSTemplateFormatVersion: "2010-09-09"
   Transform: AWS::Serverless-2016-10-31
   Description: >
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
         BucketName: "tmbinfo"

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
         Policies:
           - Version: "2012-10-17"
             Statement:
               - Effect: Allow
                 Action:
                   - "s3:PutObject"
                 Resource: "arn:aws:s3:::tmbinfo/*"

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
       Description: "TMB Bucket"
       Value: !Ref TMBBucket
     TMBGetRoute:
       Description: "TMB Get Route"
       Value: !GetAtt TMBGetRoute.Arn
     TMBGetRouteUrl:
       Description: "URL of the Lambda Function"
       Value: !GetAtt TMBGetRouteUrl.FunctionUrl
   ```

### Step 3: Deploy the SAM Application

1. **Initialize SAM CLI**:
   Ensure you have the AWS SAM CLI installed. If not, install it following the instructions [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

2. **Build the SAM application**:

   ```sh
   sam build
   ```

3. **Deploy the SAM application**:
   ```sh
   sam deploy --guided
   ```
   Follow the prompts to specify stack name, AWS region, and other parameters.

### Step 4: Retrieve and Test the Function URL

1. **Retrieve the Function URL**:
   After deployment, check the CloudFormation stack outputs in the AWS Management Console or use the following command to get the Function URL:

   ```sh
   aws cloudformation describe-stacks --stack-name <your-stack-name> --query "Stacks[0].Outputs[?OutputKey=='TMBGetRouteUrl'].OutputValue" --output text
   ```

2. **Test the Function URL**:
   Use `curl` or Postman to test the function URL:

   **Using `curl`**:

   ```sh
   curl -X POST <Function URL> -H "Content-Type: application/json" -d '{
     "home_location": {
       "latitude": 41.423043,
       "longitude": 2.184006
     },
     "work_location": {
       "latitude": 41.406232,
       "longitude": 2.192273
     }
   }'
   ```

   **Using Postman**:

   - Set the request type to `POST`.
   - Enter the Function URL as the endpoint.
   - Set the `Content-Type` header to `application/json`.
   - In the body section, select `raw` and `JSON` format, then enter the JSON payload:
     ```json
     {
       "home_location": {
         "latitude": 41.423043,
         "longitude": 2.184006
       },
       "work_location": {
         "latitude": 41.406232,
         "longitude": 2.192273
       }
     }
     ```
   - Click `Send`.

### Future Steps

1. **Add Error Handling and Logging**:

   - Enhance the Lambda function to include better error handling and logging for debugging purposes.

2. **Secure the Function URL**:

   - Consider adding authentication and authorization to secure the Lambda Function URL.

3. **Optimize Performance**:

   - Review and optimize the Lambda function performance, including memory and timeout settings based on usage patterns.

4. **Automate Tests**:
   - Add automated tests to ensure the functionality works as expected in different scenarios.

By following these steps, you will have a fully functional Lambda function that retrieves a journey plan from an API and stores it in an S3 bucket, accessible via a public URL.
