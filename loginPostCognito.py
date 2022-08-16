import os
import json
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from dateutil.tz import gettz
import base64, hashlib
import hmac
import cognitojwt
from cognitojwt.exceptions import CognitoJWTException
from botocore.exceptions import ClientError
import urllib.parse
from urllib.parse import unquote

#htmlbase is the beginning of the html output
htmlbase = ''' <!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <style type="text/css">
        body{ font: 14px sans-serif; }
        .wrapper{ width: 450px; padding: 20px; }
    </style>
    
    <title>MySite authenticated</title>
  </head>
  <body>
  <div class="wrapper">
  <h1>MySite login page</h1><br>
'''
   
htmlend = '''
    <p> 
    </body>
</html>'''

#parameters for cognito
REGION = 'us-east-1'
USERPOOL_ID = 'us-east-1_A2ABC3dYZ'
APP_CLIENT_ID = '1ab2c3defgh4ijklm5no6pqr7st'

#now and datedisplay are reused several times 
now = datetime.now(gettz("Pacific/Auckland"))
datedisplay = now.strftime("%d-%m-%Y %H:%M")

htmlbody = htmlbase.replace("datetoday", datedisplay)

#this is for the main page html
def mainpage():
    htmllogin = '''
    <div class="container py-5 px-2 bg-primary">
                <div class="row py-5 px-4">
                    <div class="col-sm-6 text-center text-md-left">
                        <h1 class="mb-3 mb-md-0 text-white text-uppercase font-weight-bold">Logged in heading</h1>
                    </div>
                    <div class="col-sm-6 text-center text-md-right">
                        <div class="d-inline-flex pt-2">
                            <h4 class="m-0 text-white"><a class="text-white" href="">Home</a></h4>
                            <h4 class="m-0 text-white px-2">/</h4>
                            <h4 class="m-0 text-white">Logged in stuff</h4>
                        </div>
                    </div>
                </div>
            </div>
    '''
    htmlcore=htmlbody + htmllogin
    return htmlcore

accesstok=''

def lambda_handler(event, context):
    #print(event)
    #first split the params passed in the form. 
    formparams = dict()

    form_data=str(event['body'])
    form_list = form_data.split("&")
    #print("form_data:", form_data)
    
    for pair in form_list:
        pairsplit=pair.split("=")
        nameitem=pairsplit[0]
        namevalue=pairsplit[1]
        formparams[nameitem] = namevalue

    #login has username and password. It passes an access token header back
    #example form_data: formtype=login&username=bob&password=mypass234

    formtype=formparams['formtype']
    if formtype == "login":
        username=formparams['username']
        password=formparams['password']
        #decode any html'ified special characters
        username = unquote(username)
        password = unquote(password)
        
        #cognito query 
        client = boto3.client('cognito-idp')
        try:
            response = client.initiate_auth(
                ClientId=APP_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            authresult = response['AuthenticationResult']
            accesstok = authresult['AccessToken']
            #htmlcore="<br><br><br><h2>" + username + " logged in</h2>"
            mainhtml=mainpage()
        except:
            #cognito failed to auth
            mainhtml="<br><br><br><h2>unauthorized</h2>"
            accesstok=''

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
            "Authorization": accesstok
        },
        "body": htmlbody + "<h4>user:" + username + "</h4>" + mainhtml  + htmlend
    }
