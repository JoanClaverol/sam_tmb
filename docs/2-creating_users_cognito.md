Great choice! Setting up Amazon Cognito with API Gateway for secure access to your Lambda function can be a bit complex, but I'll guide you through the process step by step. We'll accomplish everything using the AWS SAM (`template.yaml`) template.

### **Step 1: Create a Cognito User Pool**

The first step is to create a Cognito User Pool. This will handle user management and authentication.

In your `template.yaml`:

```yaml
Resources:
  CognitoUserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      UserPoolName: TMBUserPool
      AutoVerifiedAttributes:
        - email
      Policies:
        PasswordPolicy:
          MinimumLength: 8
          RequireUppercase: true
          RequireLowercase: true
          RequireNumbers: true
          RequireSymbols: false
```

**Explanation:**

- **UserPoolName**: This is the name of your user pool (e.g., `TMBUserPool`).
- **AutoVerifiedAttributes**: This automatically verifies email addresses for users.
- **Policies**: Here, you can enforce password strength requirements.

### **Step 2: Create a Cognito User Pool Client**

Next, create a User Pool Client. This client will interact with the user pool to authenticate users and generate JWT tokens.

In your `template.yaml`:

```yaml
Resources:
  CognitoUserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref CognitoUserPool
      ClientName: TMBUserPoolClient
      GenerateSecret: false
      AllowedOAuthFlows:
        - implicit
      AllowedOAuthScopes:
        - email
        - openid
      SupportedIdentityProviders:
        - COGNITO
      CallbackURLs:
        - https://example.com/callback
      LogoutURLs:
        - https://example.com/logout
```

**Explanation:**

- **UserPoolId**: Links the client to the user pool created in Step 1.
- **GenerateSecret**: Set to `false` because we're using a public client.
- **AllowedOAuthFlows**: Specifies the OAuth 2.0 flow type, `implicit` is typically used for web and mobile apps.
- **AllowedOAuthScopes**: Determines what information the JWT will contain (e.g., `email`, `openid`).
- **SupportedIdentityProviders**: We’re using Cognito as the identity provider.
- **CallbackURLs** and **LogoutURLs**: These are the URLs that Cognito will redirect to after authentication and logout. Replace these with your actual URLs.

### **Step 3: Create an API Gateway Integrated with Cognito**

Now, let’s create an API Gateway that uses the Cognito User Pool for authentication.

In your `template.yaml`:

```yaml
Resources:
  TMBApi:
    Type: AWS::Serverless::Api
    Properties:
      Name: TMB API
      StageName: Prod
      Auth:
        DefaultAuthorizer: CognitoAuthorizer
        Authorizers:
          CognitoAuthorizer:
            UserPoolArn: !GetAtt CognitoUserPool.Arn
      DefinitionBody:
        openapi: 3.0.1
        info:
          title: "TMB API"
          version: "1.0"
        paths:
          /get-route:
            get:
              x-amazon-apigateway-integration:
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${TMBGetRoute.Arn}/invocations
                httpMethod: POST
                type: aws_proxy
              responses: {}
```

**Explanation:**

- **Auth**: This section configures Cognito as the default authorizer for the API.
- **UserPoolArn**: Specifies the ARN of the Cognito User Pool to use for authentication.
- **/get-route**: Defines an API route that triggers the `TMBGetRoute` Lambda function. The `CognitoAuthorizer` ensures that only authenticated users can invoke this route.

### **Step 4: Define the Lambda Function**

Ensure your `TMBGetRoute` Lambda function is defined and ready to be triggered by the API Gateway.

In your `template.yaml`:

```yaml
Resources:
  TMBGetRoute:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: tmb_get_route/
      Description: TMB Get Route from API in JSON format
      Handler: app.lambda_handler
      Runtime: python3.9
      Architectures:
        - x86_64
      Environment:
        Variables:
          BucketName: !Ref TMBBucket
          SecretName: !Ref TMBSecrets
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
              Resource: !Ref TMBSecrets
```

**Explanation:**

- This Lambda function will be triggered by the API Gateway route `/get-route`, as defined in Step 3.

### **Step 5: Deploy the SAM Template**

Now that your `template.yaml` is fully defined, you can deploy it using AWS SAM.

1. **Package your application**:

   ```bash
   sam package --template-file template.yaml --s3-bucket your-s3-bucket-name --output-template-file packaged.yaml
   ```

2. **Deploy your application**:

   ```bash
   sam deploy --template-file packaged.yaml --stack-name tmb-api-stack --capabilities CAPABILITY_IAM
   ```

**Explanation:**

- **sam package**: Packages your application and uploads it to an S3 bucket.
- **sam deploy**: Deploys the packaged application to AWS.

### **Step 6: Test the Setup**

After deployment:

1. **Create a User in the Cognito User Pool**:

   - You can create users through the AWS Management Console or programmatically using the AWS CLI or SDKs.

2. **Authenticate the User**:

   - Use the Cognito Hosted UI or the AWS Amplify library to authenticate the user and retrieve a JWT token.

3. **Access the Secure API**:
   - Make a request to the `/get-route` endpoint of the API Gateway with the JWT token in the `Authorization` header.

```bash
curl -X GET https://your-api-id.execute-api.region.amazonaws.com/Prod/get-route \
-H "Authorization: Bearer your-jwt-token"
```

### Summary

By following these steps, you’ve:

- Set up a Cognito User Pool for managing users.
- Integrated the Cognito User Pool with an API Gateway to secure your Lambda function.
- Defined everything in your `template.yaml` for easy deployment with AWS SAM.

This method ensures that only authenticated users can trigger your `TMBGetRoute` Lambda function, providing a secure and scalable solution.

# OTher notes

client id

```
14mnvu7eu8qcff6u6mv5gm6f61
```

```
https://tmbgetroute.auth.eu-west-3.amazoncognito.com/login?client_id=14mnvu7eu8qcff6u6mv5gm6f61&response_type=token&scope=email+openid&redirect_uri=https://example.com/callback
```
