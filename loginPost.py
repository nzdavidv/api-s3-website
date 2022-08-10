import os
import json
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from dateutil.tz import gettz
import base64, hashlib
import bcrypt
from Crypto import Random
from Crypto.Cipher import AES
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

htmluseradd = '''
    <br><br>
        <h3>add new user form</h3>
        <p>Please enter username and password</p>
        <form action="https://www2.nzvink.com/login" method="post">
            <input type="hidden" name="formtype" value="newuser">
            <div class="form-group">
                <label>new username</label>
                <input type="text" name="newusername" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>new password</label>
                <input type="password" name="newpassword" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>admin user</label>
                <input type="text" name="username" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>admin password</label>
                <input type="password" name="password" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="create new user">
            </div>
        </form>
    </div>
'''
   
#htmlend is the end of the html output
htmlend = '''
    <p> 
    </body>
</html>'''

#table1 is users table with username, passhash pairs
dynamodb1 = boto3.resource('dynamodb')
table1 = dynamodb1.Table('mysiteusers')

#DecimalEncoder is needed for DynamoDB to work
class DecimalEncoder(json.JSONEncoder):
    '''Helper class to convert a DynamoDB item to JSON'''

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

#AESCipher is magic for encrypting and decrypting
class AESCipher():
    def __init__(self, key):
        self.private_key = hashlib.sha256(key.encode()).digest()
        self.bs = AES.block_size

    def encrypt(self, data):
        # generate public key
        public_key = Random.new().read(self.bs)

        # setup AES Cipher using public key and private key
        cipher = AES.new(self.private_key, AES.MODE_CBC, public_key)

        # enrpyt the data and convert to base64
        return base64.b64encode(public_key + cipher.encrypt(self.pad(data).encode()))

    def decrypt(self, enc):
        # convert encrypted data to base 64
        enc = base64.b64decode(enc)

        # get public key
        public_key = enc[:AES.block_size]

        # setup AES Cipher using public and private key
        cipher = AES.new(self.private_key, AES.MODE_CBC, public_key)

        # decrypt data using the public key
        return self.unpad(cipher.decrypt(enc[AES.block_size:])).decode("utf-8")

    def pad(self, s):
        # pads data so that it's a multiple of 16
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def unpad(self, s):
        # removes padding
        return s[:-ord(s[len(s)-1:])]

#usercheck needs a rewrite to be reusable.
#the code below is for useradd only and checks if a username is already used
def usercheck(usernamegiven):
    try:
        response1 = table1.query(
            KeyConditionExpression=Key('username').eq(usernamegiven)
        )
        for j in response1['Items']:
            userfound=j['username']
        if userfound == usernamegiven:
            htmlout = "fail user name " + usernamegiven + " already used"
    except:
        htmlout = "user name " + usernamegiven + " ok"
    
    return htmlout

#writetodd creates a new user and should be renamed dduseradd 
def writetodd(newusername, newpasshash):
    try:
        print(newusername, newpasshash)
        table1.put_item(
            Item={
                'username': newusername,
                'passhash': newpasshash
                }
        )
        htmlout = "user name " + newusername + " added"
    except:
        htmlout = "user name " + newusername + " fail to add"
    
    return htmlout

#checkpasswd checks if the password matches the hashed password
def checkpasswd(usernamegiven, passwd):
    #lookup the passhash in DD table
    try:
        response1 = table1.query(
            KeyConditionExpression=Key('username').eq(usernamegiven)
        )
        for j in response1['Items']:
            hashpass=j['passhash']
        #print(usernamegiven, hashpass)
    except:
        print(usernamegiven, "get password fail")
        htmlout = usernamegiven + " fail"

    #check if the hashpass matches the password
    try:
        if bcrypt.checkpw(bytes(passwd.encode('utf-8')), bytes(hashpass.encode('utf-8'))):
            #print(usernamegiven, "match")
            htmlout=usernamegiven + " match"
        else:
            #print(usernamegiven, "does not match")
            htmlout=usernamegiven + " fail"
    except:
        print(usernamegiven, "bcrypt fail")
        htmlout = usernamegiven + " fail"
        
    return htmlout

def lambda_handler(event, context):
    #print(event)
    #first split the params passed in the form. 
    #going to turn the pairs into macnames
    formparams = dict()

    #example params: formtype=newuser&newusername=bob&newpassword=gsx400x&username=davidv&password=PillowBot3
    form_data=str(event['body'])
    form_list = form_data.split("&")
    
    #list1 = ["formtype=newuser","newusername=bob","newpassword=test2345","username=davidv","password=password2"]
    for pair in form_list:
        pairsplit=pair.split("=")
        nameitem=pairsplit[0]
        namevalue=pairsplit[1]
        formparams[nameitem] = namevalue

        #print(s)

    username=formparams['username']
    password=formparams['password']
    formtype=formparams['formtype']
    try:
        newusername=formparams['newusername']
        newpassword=formparams['newpassword']
        #create a password hash from the password.
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(newpassword.encode('utf-8'), salt)
    except:
        newusername=''
        newpassword=''
    
    
    #depending on the form type is the action.
    if formtype == "newuser":
        #newuser form. check the password
        passcheckoutput=checkpasswd(username, password)

        # if it's a new user check the user doesn't already exist
        try:
            usercheckoutput=usercheck(newusername)
        except:
            usercheckoutput='fail'
            
        if 'fail' in passcheckoutput:
            htmlcore="<br><br><br><h2>unauthorized</h2>"
        else:
            #useradd form. password checks out.
            #if usercheck failed don't try and add the user
            if 'fail' in usercheckoutput:
                htmlcore="Fail username " + username + usercheckoutput
            else:
                #create the new user
                hashed_str = hashed.decode()
                htmlcore=writetodd(newusername, hashed_str)
                print("user to create is",username)
                
    elif formtype == "login":
        #if it's a login form check the password matches
        passcheckoutput=checkpasswd(username, password)
        if 'fail' in passcheckoutput:
            #htmlcore="Fail username " + username + passcheckoutput
            htmlcore="<br><br><br><h2>unauthorized</h2>"
        else:
            tnow = datetime.now(gettz("UTC"))
            tokennow = tnow.strftime("%s")

            #if the login worked assemble a code to be used in the website
            #the cipher is an agreed string both ends use to encrypt / decrypt
            cipher = AESCipher("abcdefghij123456789")
            urlstringraw="tokennow=" + tokennow
            urlstring = cipher.encrypt(urlstringraw)
            urlstringdecoded = urlstring.decode()        
            urlstringsafe=urllib.parse.quote(urlstringdecoded)
            htmlcore='<br><h4><a href=otherpage?enco=' + urlstringsafe + ">Second page</a></h4><br>" + htmluseradd
            
    else:
        htmlcore="unknown form type: " + formtype

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": htmlbase + "<h4>user:" + username + "</h4>" + htmlcore  + htmlend
    }
