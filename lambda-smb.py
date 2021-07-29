"""
Purpose:

Connects AWS Lambda to a SMB share running on Windows Server or AWS FSX for Windows. 
Once connected, it will attempt to download a file from a s3 bucket and write it to 
the SMB share specified in SeceretsManager.
"""

import json
import boto3
import base64
import os
from botocore.exceptions import ClientError
from smb.SMBConnection import SMBConnection
def lambda_handler(event, context):
    #Call function to get file share secrets from AWS Secrets Manager
    secret = get_secret(event)
    json_string = json.loads(secret['SecretString'])
    #Remember: dict.get's are from secrets manager and events are from lambda input
    dict = json.loads(secret['SecretString'])
    domain = dict.get("domain")
    username = dict.get("username")
    password = dict.get("password")
    client = ""
    server_name = dict.get("hostname")
    server_ip = dict.get("ip")
    port = int(dict.get("port"))
    ### Source file
    s3_bucket = "cigna-smb-test"
    filename = event['sourceFile']
    tmp_dir = "/tmp"
    tmp_file = tmp_dir + "/" + filename
    ### FSX Share
    dest_share = dict.get("destShare")
    dest_dir = dict.get("destFolder")
    dest_file = dest_dir + "/" + filename
    ### SMB Connection
    conn = None
    print('Attempting to establish SMB connection to destination file share.')
    print("Troubleshoot:" ,username,password,client,server_name,domain,server_ip,port)
    #Attempt to establish SMB connection to destination file share
    try:
        if domain is not None:
            conn = SMBConnection(username, password, client, server_name, domain=domain, use_ntlm_v2=True, is_direct_tcp=True)
        else:
            conn = SMBConnection(username, password, client, server_name, use_ntlm_v2=True, is_direct_tcp=True)
            print("The password is" ,password)
        if server_ip is not None:
            connected = conn.connect(server_ip, port)
            print("Using IP to connect")
        else:
            connected = conn.connect(server_name, port)
            print("Using Hostname to connect")
        if connected:
            print('Successfully connected to destination share.')
    except Exception as e:
        print('Error connecting to destination file share.')
        raise e
    print('Attempting to download source file from Amazon S3.')
    #Copy source file from s3
    try:
        s3 = boto3.client('s3')
        objects3tmp = s3.download_file(s3_bucket, filename, tmp_file)
        print('Successfully downloaded file to local temp directory ' + tmp_dir + '.')
        #open rb (read binary)
        file_obj = open(tmp_file, 'rb')
    except Exception as e:
        print('Error downloading file from S3. Check S3 permissions.')
        raise e
    print('Checking to see if destination directory already exists.')
    #Check to see if the destination directory exists. Create it if it does not
    try:
        files = conn.listPath(dest_share, dest_dir)
        print('Destination directory exists.')
    except:
        print('Unable to list files in destination directory. Directory most likely does not exist so we will attempt to create it.')
        conn.createDirectory(dest_share, dest_dir)
    print('Attempting to copy file to destination file share.')
    #Write the file to the destination share and close the SMB connection
    try:
        conn.storeFile(dest_share, dest_file, file_obj)
        conn.close()
        print('File successfully copied to destination file share and connection closed.')
    except:
        print('Error writing file to destination file share.')
    print('Cleaning things up...')
    #Delete local temp file to clean things up
    try:
        os.remove(tmp_file)
        print('Successfully deleted source file from local temp directory.')
    except:
        print('Error deleting source file from local temp directory.')
#Get the file share credentials from AWS Secrets Manager
def get_secret(event):
    print('Attempting to get credentials and parameters from AWS Secrets Manager.')
    secret_name = event['smName']
    region_name = event['smRegion']
    print(secret_name)
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
        print('Successfully obtained credentials from AWS Secrets Manager.')
        return get_secret_value_response
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
