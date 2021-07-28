# Lambda SMB Function
Connect AWS Lambda to a SMB share running on Windows Server or AWS FSX for Windows

## Requirements
* Python packages shown in requirements.txt
* PySMB module files *MUST* be included in the Lambda function upload
    ```
    pip3 install pysmb --target lambda/pysmb
    ```