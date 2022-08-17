import json
import os
import base64
import hashlib
import hmac
import logging
import boto3
from io import BytesIO

s3 = boto3.resource('s3')

bucketname = os.environ['BUCKETNAME']

bucket = s3.Bucket(bucketname)

html=''

def readhtmlfile(filename):
    filehand = s3.Object(bucketname,filename)
    body = filehand.get()['Body'].read()
    html=body.decode('utf8')
    return html
    
def readbinfile(filename):
    filehand = s3.Object(bucketname,filename)
    file_byte_string = filehand.get()['Body'].read()
    return Image.open(BytesIO(file_byte_string))

def lambda_handler(event, context):
    
    filereq = event['rawPath']
    filereqn=filereq[1:]
    if ('.htm' in filereq) or ('.js' in filereq):
        reads3out=readhtmlfile(filereqn)
        html=reads3out
    else:
        if filereqn == "":
            reads3out=readhtmlfile('index.html')
            html=reads3out
        else:
            html=reads3out
            
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": html
    }
