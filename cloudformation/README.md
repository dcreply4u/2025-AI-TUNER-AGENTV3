# CloudFormation Templates for AI Tuner Agent

This directory contains AWS CloudFormation templates for deploying the AI Tuner Agent cloud infrastructure.

## Templates Overview

### 01-main-stack.yaml
**Main Infrastructure Stack**

Creates the core AWS resources for the AI Tuner Agent:

- **S3 Buckets:**
  - `TelemetryDataBucket`: Stores telemetry data logs (90-day retention, transitions to IA after 30 days)
  - `VideoStorageBucket`: Stores video recordings from cameras (180-day retention, transitions to Glacier after 90 days)

- **DynamoDB Tables:**
  - `TelemetryTable`: Stores real-time telemetry data (device_id + timestamp)
  - `GPSHistoryTable`: Stores GPS location history with timestamp index
  - `PerformanceRunsTable`: Stores performance run data (0-60, quarter-mile, etc.)

- **IAM Roles:**
  - `LambdaExecutionRole`: Role for Lambda functions with permissions for DynamoDB, S3, IoT Core, and CloudWatch Logs

- **CloudWatch Log Groups:**
  - Telemetry logs (30-day retention)
  - API logs (30-day retention)

- **KMS Encryption:**
  - Encryption key and alias for data encryption

**Deployment Order:** Deploy this stack first.

### 02-iot-core-stack.yaml
**IoT Core Stack**

Sets up AWS IoT Core for MQTT telemetry streaming:

- **IoT Policies:**
  - Device policy for connecting and publishing telemetry data

- **IoT Topic Rules:**
  - `TelemetryTopicRule`: Automatically stores telemetry messages in DynamoDB
  - `GPSTopicRule`: Stores GPS fixes in GPS history table

- **IAM Roles:**
  - `IoTDynamoDBRole`: Allows IoT Core to write to DynamoDB tables

- **IoT Thing Management:**
  - Thing Type for vehicle devices
  - Thing Group for organizing vehicles

**Deployment Order:** Deploy this stack after the main stack (depends on DynamoDB table exports).

## Deployment Instructions

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS account with permissions to create:
   - S3 buckets
   - DynamoDB tables
   - IAM roles and policies
   - IoT Core resources
   - KMS keys
   - CloudWatch Log Groups

### Step 1: Deploy Main Stack

```bash
aws cloudformation create-stack \
  --stack-name ai-tuner-main-stack \
  --template-body file://01-main-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=ai-tuner \
    ParameterKey=Environment,ParameterValue=production \
    ParameterKey=AdminUsername,ParameterValue=your-admin-username \
    ParameterKey=AdminPassword,ParameterValue=your-secure-password \
    ParameterKey=AllowedCIDR,ParameterValue=0.0.0.0/0 \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack to complete
aws cloudformation wait stack-create-complete --stack-name ai-tuner-main-stack
```

### Step 2: Get Lambda Execution Role ARN

```bash
# Get the Lambda Execution Role ARN from stack outputs
LAMBDA_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ai-tuner-main-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaExecutionRoleArn`].OutputValue' \
  --output text)

echo "Lambda Role ARN: $LAMBDA_ROLE_ARN"
```

### Step 3: Deploy IoT Core Stack

```bash
aws cloudformation create-stack \
  --stack-name ai-tuner-iot-stack \
  --template-body file://02-iot-core-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=ai-tuner \
    ParameterKey=Environment,ParameterValue=production \
    ParameterKey=LambdaExecutionRoleArn,ParameterValue=$LAMBDA_ROLE_ARN

# Wait for stack to complete
aws cloudformation wait stack-create-complete --stack-name ai-tuner-iot-stack
```

### Step 4: Get IoT Endpoint

```bash
# Get the IoT Core endpoint
IOT_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name ai-tuner-iot-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`IoTEndpoint`].OutputValue' \
  --output text)

echo "IoT Endpoint: $IOT_ENDPOINT"
```

## Updating Stacks

To update an existing stack:

```bash
aws cloudformation update-stack \
  --stack-name ai-tuner-main-stack \
  --template-body file://01-main-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=ai-tuner \
    ParameterKey=Environment,ParameterValue=production \
  --capabilities CAPABILITY_NAMED_IAM
```

## Deleting Stacks

**Important:** Delete stacks in reverse order (IoT stack first, then main stack).

```bash
# Delete IoT stack first
aws cloudformation delete-stack --stack-name ai-tuner-iot-stack
aws cloudformation wait stack-delete-complete --stack-name ai-tuner-iot-stack

# Then delete main stack
aws cloudformation delete-stack --stack-name ai-tuner-main-stack
aws cloudformation wait stack-delete-complete --stack-name ai-tuner-main-stack
```

## Configuration

### Environment Variables

After deployment, configure your edge device with:

```bash
export AWS_ENDPOINT="<your-iot-endpoint>"
export AWS_PORT="8883"
export TOPIC="ai-tuner/telemetry/car001"
```

### Device Certificates

1. Create an IoT Thing in AWS IoT Console
2. Generate device certificates
3. Download and place on device:
   - `AmazonRootCA1.pem`
   - `device-cert.pem`
   - `private-key.pem`
4. Attach the IoT policy created by the stack to the Thing

## Cost Considerations

- **S3:** Pay for storage and requests (lifecycle rules help manage costs)
- **DynamoDB:** Pay-per-request billing mode (scales automatically)
- **IoT Core:** Pay per message (first 250K messages/month free)
- **CloudWatch Logs:** Pay for ingestion and storage
- **KMS:** $1/month per key + $0.03 per 10K requests

## Security Notes

- S3 buckets have public access blocked
- All data encrypted at rest (S3 SSE, DynamoDB encryption, KMS)
- IoT Core uses mutual TLS authentication
- IAM roles follow least-privilege principle
- Change default passwords before production use

## Troubleshooting

### Stack Creation Fails

- Check IAM permissions
- Verify S3 bucket names are globally unique
- Ensure DynamoDB table names don't conflict

### IoT Connection Issues

- Verify device certificates are valid
- Check IoT policy permissions
- Ensure device ID matches Thing name pattern

### Data Not Appearing in DynamoDB

- Check IoT Topic Rules are enabled
- Verify IoT role has DynamoDB write permissions
- Check CloudWatch Logs for errors

## Support

For issues or questions, refer to:
- AWS CloudFormation documentation
- AWS IoT Core documentation
- Project documentation in `docs/` directory

