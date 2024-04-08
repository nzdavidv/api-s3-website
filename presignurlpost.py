import json
import os
import logging
import boto3
import textwrap 


#s3 = boto3.resource('s3')
bucketname = os.environ['BUCKETNAME']
s3url = "https://" + bucketname + ".s3.amazonaws.com/"

# Initialize boto3 to use the S3 client.
s3_client = boto3.client('s3')

form_data = s3_client.generate_presigned_post(
    Bucket= bucketname,
    Key= r'${filename}',
    ExpiresIn = 3600)

def displaypsk():
    localhtmlout=''
    for k, v in form_data['fields'].items():
        localhtmlout=localhtmlout + '             <input type="hidden" name="' + k + '" value="' + v + '" />\n'
    
    return localhtmlout


#print(str(form_data))

htmlstart='''
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    </head>
    <body>
'''

htmlformaction='<form action="' + s3url + '" method="post" \n enctype="multipart/form-data">'

htmlend='''
            <input type="file"   name="file" /> <br />
            <input type="submit" name="submit" value="Upload to object storage" />
        </form>
</html>
'''

def lambda_handler(event, context):
    htmlpsk=displaypsk()
    html = htmlstart + htmlformaction + htmlpsk + htmlend

    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'text/html' },
        'body': html
    }
