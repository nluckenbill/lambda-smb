# Lambda SMB Function
Connects AWS Lambda to a SMB share running on Windows Server or AWS FSX for Windows. Once connected, it will attempt to download a file from a s3 bucket and write it to the SMB share specified in SeceretsManager.

## Requirements
* Python packages shown in requirements.txt
* PySMB module files *MUST* be included in the Lambda deployment package root folder
    ```
    pip3 install pysmb --target .
    ```
* SecretsManager setup with input parameters
* Lambda Function role has read access to SecretsManager and S3 bucket
* VPC has SecretsManager and S3 Endpoint connected

## Example Lambda input
    {
    "smName": "fsxshare",
    "smRegion": "us-west-1",
    "s3Bucket": "cigna-smb-test",
    "sourceFile": "test.txt"
    }