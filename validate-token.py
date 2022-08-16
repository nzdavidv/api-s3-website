import base64
import hashlib
import hmac
import logging
import boto3
import cognitojwt

from botocore.exceptions import ClientError

id_token = 'eyJraWQiOiJ0Y1Z0S1dtalNLNFZIc3pJN2lcbiglongtoken'
REGION = 'us-east-1'
USERPOOL_ID = 'us-east-1_A2ABC3dYZ'
APP_CLIENT_ID = '1ab2c3defgh4ijklm5no6pqr7st'

# Sync mode
verified_claims: dict = cognitojwt.decode(
    id_token,
    REGION,
    USERPOOL_ID,
    app_client_id=APP_CLIENT_ID,  # Optional
    testmode=True  # Disable token expiration check for testing purposes
)

print(verified_claims)
