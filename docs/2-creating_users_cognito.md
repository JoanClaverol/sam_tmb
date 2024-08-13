### Summary: Implementing Cognito and JWT Integration with AWS Lambda

This document provides a step-by-step guide on how to implement AWS Cognito for user authentication and use JWT (JSON Web Tokens) to secure API Gateway endpoints that invoke AWS Lambda functions. This guide is based on the provided `template.yaml` and includes necessary changes to the `app.py` file.

---

### **Step 1: Set Up Cognito User Pool**

1. **Create a Cognito User Pool**:

   - **Purpose**: The User Pool is where your users are stored and authenticated.
   - **Configuration**:
     - Set `UserPoolName` to `TestingUsers`.
     - Enable email as a username attribute.
     - Configure auto-verification via email.
     - Set up a password policy (e.g., minimum length, require uppercase).

   Example:

   ```yaml
   UserPool:
     Type: AWS::Cognito::UserPool
     Properties:
       AdminCreateUserConfig:
         AllowAdminCreateUserOnly: false
       UserPoolName: TestingUsers
       UsernameAttributes:
         - email
       AutoVerifiedAttributes:
         - email
       Policies:
         PasswordPolicy:
           MinimumLength: 6
           RequireUppercase: true
           RequireLowercase: true
   ```

2. **Create a Cognito User Pool Client**:

   - **Purpose**: The User Pool Client allows the app to interact with the User Pool (e.g., to log in users).
   - **Configuration**:
     - Associate the client with your User Pool.
     - Disable secret generation (simplifies login for this example).
     - Enable `USER_PASSWORD_AUTH` flow.

   Example:

   ```yaml
   UserPoolTokenClient:
     Type: AWS::Cognito::UserPoolClient
     Properties:
       UserPoolId: !Ref UserPool
       GenerateSecret: false
       ExplicitAuthFlows:
         - USER_PASSWORD_AUTH
   ```

3. **Create an Initial Cognito User**:

   - **Purpose**: Automatically create a user during deployment for testing.
   - **Configuration**:
     - Set `DesiredDeliveryMediums` to `EMAIL` to send the user their temporary password.
     - Use the email provided as a parameter.

   Example:

   ```yaml
   UserPoolUser:
     Type: AWS::Cognito::UserPoolUser
     Properties:
       Username: !Ref YourEmail
       UserPoolId: !Ref UserPool
       DesiredDeliveryMediums:
         - EMAIL
   ```

---

### **Step 2: Set Up API Gateway with Cognito Authorization**

1. **Create an API Gateway**:

   - **Purpose**: Expose your Lambda functions via HTTP endpoints.
   - **Configuration**:
     - Define `Cors` settings to allow cross-origin requests.
     - Attach a Cognito authorizer that uses your User Pool.

   Example:

   ```yaml
   TMBApi:
     Type: AWS::Serverless::Api
     Properties:
       Name: ServiceApi
       StageName: !Ref Version
       Cors:
         AllowMethods: "'*'"
         AllowHeaders: "'*'"
         AllowOrigin: "'*'"
       Auth:
         Authorizers:
           CognitoAuthorizer:
             UserPoolArn: !GetAtt UserPool.Arn
   ```

---

### **Step 3: Create Lambda Functions**

1. **Open (Unauthenticated) Lambda Function**:

   - **Purpose**: A publicly accessible endpoint that doesn’t require authentication.
   - **Configuration**:
     - Attach the function to an API Gateway path (`/open`) without any authorizer.

   Example:

   ```yaml
   TMBGetRoute:
     Type: AWS::Serverless::Function
     Properties:
       CodeUri: tmb_get_route/
       Description: TMB Get Route from API in JSON format
       Handler: app.lambda_handler
       Runtime: python3.9
       Environment:
         Variables:
           BucketName: !Ref BucketName
           SecretName: !Ref TMBSecrets
       Policies:
         - Version: "2012-10-17"
           Statement:
             - Effect: Allow
               Action:
                 - s3:PutObject
               Resource: !Sub arn:aws:s3:::${BucketName}/*
             - Effect: Allow
               Action:
                 - secretsmanager:GetSecretValue
               Resource: !Ref TMBSecrets
       Events:
         Get:
           Type: Api
           Properties:
             Path: /open
             RestApiId: !Ref TMBApi
             Method: GET
   ```

2. **Authenticated Lambda Function**:

   - **Purpose**: A protected endpoint that requires users to be authenticated via Cognito.
   - **Configuration**:
     - Attach the function to an API Gateway path (`/`) with the Cognito authorizer.

   Example:

   ```yaml
   TMBGetRoute:
     Type: AWS::Serverless::Function
     Properties:
       CodeUri: tmb_get_route/
       Description: TMB Get Route from API in JSON format
       Handler: app.lambda_handler
       Runtime: python3.9
       Environment:
         Variables:
           BucketName: !Ref BucketName
           SecretName: !Ref TMBSecrets
       Policies:
         - Version: "2012-10-17"
           Statement:
             - Effect: Allow
               Action:
                 - s3:PutObject
               Resource: !Sub arn:aws:s3:::${BucketName}/*
             - Effect: Allow
               Action:
                 - secretsmanager:GetSecretValue
               Resource: !Ref TMBSecrets
       Events:
         GetAutherised:
           Type: Api
           Properties:
             Path: /
             RestApiId: !Ref TMBApi
             Method: GET
             Auth:
               Authorizer: CognitoAuthorizer
   ```

---

### **Step 4: Update the Lambda Function Code (`app.py`)**

1. **Return Proper Response Format**:

   - Ensure your Lambda function returns a response with `statusCode`, `body`, and `headers` in the format expected by API Gateway.

   Example of an updated `app.py`:

   ```python
   import json
   import requests

   def get_journey_plan(home_location, work_location, app_id, app_key):
       # Dummy implementation for journey plan retrieval
       # Replace with actual logic
       return {
           "from": home_location,
           "to": work_location,
           "route": "Sample route data"
       }

   def store_journey_plan(journey_plan):
       # Dummy implementation for storing the journey plan
       # Replace with actual storage logic
       pass

   def lambda_handler(event, context):
       """
       Lambda function handler for retrieving and storing journey plans.
       """
       try:
           HOME_LOCATION = "Home"
           WORK_LOCATION = "Work"
           TMB_APP_ID = "YourAppId"
           TMB_APP_KEY = "YourAppKey"

           journey_plan = get_journey_plan(HOME_LOCATION, WORK_LOCATION, TMB_APP_ID, TMB_APP_KEY)
           store_journey_plan(journey_plan)

           return {
               "statusCode": 200,
               "body": json.dumps({
                   "message": "Journey plan successfully retrieved",
                   "journey_plan": journey_plan,
               }),
               "headers": {
                   "Content-Type": "application/json",
                   "Access-Control-Allow-Origin": "*",
                   "Access-Control-Allow-Methods": "*",
                   "Access-Control-Allow-Headers": "*"
               }
           }

       except requests.RequestException as e:
           print(f"Request failed: {e}")
           return {
               "statusCode": 502,
               "body": json.dumps({
                   "message": "Failed to retrieve the journey plan",
                   "error": str(e)
               }),
               "headers": {
                   "Content-Type": "application/json",
                   "Access-Control-Allow-Origin": "*",
                   "Access-Control-Allow-Methods": "*",
                   "Access-Control-Allow-Headers": "*"
               }
           }

       except Exception as e:
           print(f"An error occurred: {e}")
           return {
               "statusCode": 500,
               "body": json.dumps({
                   "message": "Internal server error",
                   "error": str(e)
               }),
               "headers": {
                   "Content-Type": "application/json",
                   "Access-Control-Allow-Origin": "*",
                   "Access-Control-Allow-Methods": "*",
                   "Access-Control-Allow-Headers": "*"
               }
           }
   ```

   This updated code ensures proper error handling and returns the correct format that API Gateway expects.

---

### **Step 5: Deploy and Test**

1. **Deploy the Stack**:

   - **Use SAM CLI**:
     - Package the template and deploy it using AWS SAM.

   Commands:

   ```bash
   sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket your-deployment-bucket
   sam deploy --template-file packaged.yaml --stack-name tmb-api --capabilities CAPABILITY_IAM --parameter-overrides YourEmail=your-email@example.com
   ```

2. **Retrieve JWT Token for Testing**:

   - **Initiate Authentication**:
     - Log in using AWS CLI with the temporary password and set a new one.
   - **Get JWT Token**:
     - Run the `initiate-auth` command again with your new password to retrieve the JWT.

   Commands:

   ```bash
   AUTH_CHALLENGE_SESSION=$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --auth-parameters "USERNAME=your-email@example.com,PASSWORD=temporary-password" --client-id $(aws cloudformation describe-stacks --stack-name tmb-api --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text) --query "Session" --output text)

   aws cognito-idp admin-respond-to-auth-challenge --user-pool-id $(aws cloudformation describe-stacks --stack-name tmb-api --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text) --client-id $(aws cloudformation describe-stacks --stack-name tmb-api --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text) --challenge-responses "NEW_PASSWORD=YourNewPassword,USERNAME=your-email@example.com" --challenge-name NEW_PASSWORD_REQUIRED --session $AUTH_CHALLENGE_SESSION

   JWT_TOKEN=$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --auth-parameters "USERNAME=your-email@example.com,PASSWORD=YourNewPassword" --client-id $(aws cloudformation describe-stacks --stack-name tmb-api --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text) --query "AuthenticationResult.IdToken" --output text)
   ```

3. **Test Endpoints Using `curl`**:

   - **Open Endpoint**:
     - Test the unauthenticated endpoint.
   - **Authenticated Endpoint**:
     - Test the authenticated endpoint by passing the JWT token.

   Commands:

   ```bash
   # Test open endpoint
   curl https://your-api-id.execute-api.region.amazonaws.com/v1/open

   # Test authenticated endpoint
   curl -H "Authorization: Bearer $JWT_TOKEN" https://your-api-id.execute-api.region.amazonaws.com/v1/
   ```

---

### **Conclusion**

This guide provides detailed steps to implement AWS Cognito for user authentication and secure API Gateway endpoints using JWT tokens, integrated with Lambda functions. By following these steps, you can replicate this setup in the future, ensuring secure and authenticated access to your serverless applications.
