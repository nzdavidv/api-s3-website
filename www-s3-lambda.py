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
    s3obj = s3.Object(bucketname,filename)
    filehandle = s3obj.get()['Body'].read()
    filebytes = BytesIO(filehandle).getvalue()
    return filebytes

def lambda_handler(event, context):
    
    filereq = event['rawPath']
    filereqn=filereq[1:]
    base64line=""
    if ('.htm' in filereq) or ('.html' in filereq):
        reads3out=readhtmlfile(filereqn)
        html=reads3out
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'text/html' },
            'body': html
        }
    elif ('.js' in filereq):
        reads3out=readhtmlfile(filereqn)
        html=reads3out
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'text/javascript' }
            'body': html
        }
    elif ('.css' in filereq):
        reads3out=readhtmlfile(filereqn)
        html=reads3out
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'text/css' }
            'body': html
        }
    elif ('.jpg' in filereq) or ('.jpeg' in filereq):
        reads3out=readbinfile(filereqn) 
        html=reads3out
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'image/jpg' },
            'body': base64.b64encode(html),
            'isBase64Encoded': True
        }
    elif ('.PDF' in filereq) or ('.pdf' in filereq):
        reads3out=readbinfile(filereqn) 
        html=reads3out
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'application/pdf' },
            'body': base64.b64encode(html),
            'isBase64Encoded': True
        }
    else:
        if filereqn == "":
            reads3out=readhtmlfile('index.html')
            html=reads3out
            return {
                "statusCode": 200,
                'headers': { 'Content-Type': 'text/html' },
                'body': html
            }
        else:
            #reads3out=readbinfile(filereqn)
            reads3out=readhtmlfile(filereqn)
            html=reads3out
            return {
                "statusCode": 200,
                'headers': { 'Content-Type': 'text/html' },
                'body': html
            }
