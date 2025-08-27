# Manual Deployment Guide

Complete step-by-step instructions for deploying the K-12 Co-Teacher solution in a fresh AWS account.

## Prerequisites

- AWS account with admin access
- AWS CLI configured (`aws configure`)
- Region: **us-west-2** (recommended for Bedrock availability)
- Node.js 18+ and npm installed
- Python 3.11+ installed

## Step 1: Enable Bedrock Model Access

1. Go to [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to "Model access" → "Edit"
3. Enable: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
4. Wait for "Access granted" status

## Step 2: Create DynamoDB Tables

Create these 5 tables with **exact names** (use AWS Console or CLI):

| Table Name | Partition Key | Sort Key |
|------------|---------------|----------|
| `k12-coteacher-teachers-to-classes` | `teacherID` (String) | - |
| `k12-coteacher-class-to-students` | `classID` (String) | - |
| `k12-coteacher-student-profiles` | `studentID` (String) | - |
| `k12-coteacher-chat-history` | `TeacherId` (String) | `sortId` (String) |
| `k12-coteacher-class-attributes` | `classID` (String) | - |

The full schema of these tables can be found in **`sample_data/dynamo_data`** for reference, but only a PK needs to be configured to create the tables.

**CLI Commands:**
```bash
aws dynamodb create-table --table-name k12-coteacher-teachers-to-classes \
  --attribute-definitions AttributeName=teacherID,AttributeType=S \
  --key-schema AttributeName=teacherID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table --table-name k12-coteacher-class-to-students \
  --attribute-definitions AttributeName=classID,AttributeType=S \
  --key-schema AttributeName=classID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table --table-name k12-coteacher-student-profiles \
  --attribute-definitions AttributeName=studentID,AttributeType=S \
  --key-schema AttributeName=studentID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table --table-name k12-coteacher-chat-history \
  --attribute-definitions AttributeName=TeacherId,AttributeType=S AttributeName=sortId,AttributeType=S \
  --key-schema AttributeName=TeacherId,KeyType=HASH AttributeName=sortId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table --table-name k12-coteacher-class-attributes \
  --attribute-definitions AttributeName=classID,AttributeType=S \
  --key-schema AttributeName=classID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Step 3: Create IAM Role for Lambda Functions

Create an IAM role named `K12CoTeacherLambdaRole` with:

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Attach Policies:**
1. `AWSLambdaBasicExecutionRole` (AWS managed)
2. Custom policy for DynamoDB and Bedrock access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-west-2:*:table/k12-coteacher-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "execute-api:ManageConnections"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 4: Create Lambda Functions

Create 6 Lambda functions (Python 3.11, use the IAM role from Step 3):

### 4.1 getClassesForDashboard
- **Code**: ZIP and upload `lambdas/getClassesForDashboard/` folder
- **Environment Variables**:
  - `TEACHER_CLASSES_TABLE` = `k12-coteacher-teachers-to-classes`
  - `CLASS_ATTRIBUTES_TABLE` = `k12-coteacher-class-attributes`

### 4.2 getStudentsForClass
- **Code**: ZIP and upload `lambdas/getStudentsForClass/` folder
- **Environment Variables**:
  - `CLASS_STUDENTS_TABLE` = `k12-coteacher-class-to-students`

### 4.3 getStudentProfile
- **Code**: ZIP and upload `lambdas/getStudentProfile/` folder
- **Environment Variables**:
  - `STUDENT_PROFILES_TABLE` = `k12-coteacher-student-profiles`

### 4.4 getChatHistory
- **Code**: ZIP and upload `lambdas/getChatHistory/` folder
- **Environment Variables**:
  - `CHAT_HISTORY_TABLE` = `k12-coteacher-chat-history`

### 4.5 editStudentProfile
- **Code**: ZIP and upload `lambdas/editStudentProfile/` folder
- **Environment Variables**:
  - `STUDENT_PROFILES_TABLE` = `k12-coteacher-student-profiles`

### 4.6 inference
- **Code**: ZIP and upload `lambdas/inference/` folder
- **Timeout**: 5 minutes
- **Environment Variables**:
  - `CHAT_HISTORY_TABLE` = `k12-coteacher-chat-history`
  - `STUDENT_PROFILES_TABLE` = `k12-coteacher-student-profiles`
  - `CLASS_ATTRIBUTES_TABLE` = `k12-coteacher-class-attributes`
  - `CLASS_STUDENTS_TABLE` = `k12-coteacher-class-to-students`
  - `TEACHER_CLASSES_TABLE` = `k12-coteacher-teachers-to-classes`

## Step 5: Create REST API Gateway

1. Create a new **REST API** in API Gateway
2. Enable **CORS** for all origins
3. Create these resources and methods:

| Resource | Method | Integration |
|----------|--------|-------------|
| `/getClassesForDashboard` | POST | getClassesForDashboard Lambda |
| `/getStudentsForClass` | POST | getStudentsForClass Lambda |
| `/getStudentProfile` | POST | getStudentProfile Lambda |
| `/getHistory` | POST | getChatHistory Lambda |
| `/editStudentProfile` | POST | editStudentProfile Lambda |

4. **Deploy** the API to a stage (e.g., `dev`)
5. **Note the Invoke URL** (e.g., `https://abc123.execute-api.us-west-2.amazonaws.com/dev/`)

## Step 6: Create WebSocket API Gateway

1. Create a new **WebSocket API** in API Gateway
2. Set **Route Selection Expression**: `$request.body.action`
3. Create these routes:

| Route | Integration |
|-------|-------------|
| `$connect` | inference Lambda |
| `$disconnect` | inference Lambda |
| `$default` | inference Lambda |

4. **Deploy** to a stage (e.g., `dev`)
5. **Note the WebSocket URL** (e.g., `wss://xyz789.execute-api.us-west-2.amazonaws.com/dev`)

## Step 7: Create Cognito User Pool 

1. Create a **User Pool** with email sign-in
2. Create an **App Client** (no secret)
3. Create a **Domain** for hosted UI
4. **Note**: User Pool ID, Client ID, and Domain

## Step 8: Configure Frontend Environment

Update `frontend/.env.local`:
```bash
# API Endpoints (from Step 5)
CLASSES_API_ENDPOINT=https://YOUR_REST_API_ID.execute-api.us-west-2.amazonaws.com/dev/getClassesForDashboard
STUDENTS_API_ENDPOINT=https://YOUR_REST_API_ID.execute-api.us-west-2.amazonaws.com/dev/getStudentsForClass
STUDENT_PROFILE_API_ENDPOINT=https://YOUR_REST_API_ID.execute-api.us-west-2.amazonaws.com/dev/getStudentProfile
NEXT_PUBLIC_CHAT_HISTORY_API=https://YOUR_REST_API_ID.execute-api.us-west-2.amazonaws.com/dev/getHistory

# WebSocket (from Step 6)
NEXT_PUBLIC_WS_URL=wss://YOUR_WS_API_ID.execute-api.us-west-2.amazonaws.com/dev

# Cognito (from Step 7)
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-west-2_XXXXXXXXX
NEXT_PUBLIC_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
NEXT_PUBLIC_COGNITO_DOMAIN=your-domain-prefix
```

## Step 9: Test Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` and verify the app loads.

## Step 10: Deploy Frontend with AWS Amplify

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. **New App** → **Host web app**
3. Connect your **GitHub repository**
4. Set **Root directory**: `frontend`
5. **Add environment variables** (same as Step 8)
6. **Deploy**
7. **Note the Amplify URL**

## Step 11: Update Cognito Callback URLs

Add your Amplify URL to Cognito:
1. Go to Cognito User Pool → App Integration → App Client
2. **Edit Hosted UI**
3. Add **Callback URLs**: `https://YOUR_AMPLIFY_URL`
4. Add **Sign-out URLs**: `https://YOUR_AMPLIFY_URL/login`

## Step 12: Seed Sample Data

**Load Data from CSV files**
```bash
cd sample_data
pip install boto3
python load_csv_to_dynamo.py
```

## Troubleshooting

- **Bedrock Access Denied**: Ensure Claude 3.7 Sonnet model access is enabled
- **CORS Errors**: Verify API Gateway CORS is enabled for all origins
- **Lambda Timeouts**: Check CloudWatch logs for specific errors
- **DynamoDB Access**: Verify IAM role has correct table permissions

## Clean Up

To remove all resources:
1. Delete Amplify app
2. Delete API Gateways
3. Delete Lambda functions
4. Delete IAM role
5. Delete DynamoDB tables
6. Delete Cognito User Pool
