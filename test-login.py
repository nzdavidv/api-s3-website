import base64
import hashlib
import hmac
import logging
import boto3

from botocore.exceptions import ClientError

client = boto3.client('cognito-idp')
response = client.initiate_auth(
        ClientId='1ab2c3defgh4ijklm5no6pqr7st',
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
                'USERNAME': 'bob',
                'PASSWORD': 'NewPa33%bk'
        }
)

authresult = response['AuthenticationResult']
accesstok = authresult['AccessToken']

print(accesstok)
