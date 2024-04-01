import json
import os
import base64
import hashlib
import hmac
import logging
import boto3
from io import BytesIO
import urllib.parse
from array import array
import textwrap
import re

#clag bail until I have password auth
#return 0

#s3 = boto3.resource('s3')
bucketname = os.environ['BUCKETNAME']
#bucket = s3.Bucket(bucketname)


masterpasswd = os.environ['MPASSWD']
dbname = os.environ['DATABASE']
addsongapi = os.environ['ADDSONGAPI']
songlistapi = os.environ['SONGLISTAPI']
max_file_size = os.environ['MAXFILESIZEBYTES']

#s3url = os.environ['S3URL']  # https://nzvink-reach-int-dev.s3.amazonaws.com/         nzvink-reach-int-dev
s3url = "https://" + bucketname + ".s3.amazonaws.com/"


dynamodb1 = boto3.resource('dynamodb')
songtable = dynamodb1.Table(dbname)

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

#URL_EXPIRATION_SECONDS = 300

# Initialize boto3 to use the S3 client.
s3_client = boto3.client('s3')


htmlstart='''
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Addsong</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
        <style type="text/css">
            body{ font: 14px sans-serif; }
            .form-group{ width: 650px; padding: 10px; }
        </style>
    </head>
    <body>
'''

formstart1='        <form action="' + s3url + '" method="post" \n enctype="multipart/form-data">'

songlistlogin1='''
    <div class="wrapper">
        <form action="'''

songlistlogin2='''"method="post">
            <input type="hidden" name="formtype" value="login">
            <input type="hidden" name="password" value="'''

songlistlogin3='''"
            <div class="form-group">
            </div>
            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="back to song list">
            </div>
        </form>
    </div>
</body>
</html>
'''

addsong1='''
<div class="content">
    <br>
    <h4>Add a song</h4>
    <p>
        <form action= "'''
        
addsong2='''" method="post">
            <input type="hidden" name="formtype" value="newsong">
            <div class="form-group">
                <label>Song *</label>
                <input type="text" name="newsongname" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Last played</label>
                <input type="text" name="newsonglastplayed" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Key</label>
                <input type="text" name="newsongkey" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Key change from spotify</label>
                <input type="text" name="newsongkeydiff" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Notes</label>
                <input type="text" name="newsongnotes" class="form-control">
                <span class="help-block"></span>
            </div>

'''

addsong3='            <input type="hidden" name="password" value="' + masterpasswd + '">' 

addsong4='''
            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="Next">
            </div>
        </form>
    </p>
</div>
'''

htmlend='''
</body>
</html>
'''

def editsong(esong, elastplayed, ekey, ekeydiff, esongsheet, enotes):
    modsong1='''
    <div class="content">
        <br>
        <h4>Update song</h4>
        <p>
            <form action= "'''

    modsong2='''" method="post">
            <input type="hidden" name="formtype" value="newsong">
            <div class="form-group">
                <label>Song name (readonly)</label>
                <input type="text" name="newsongname" class="form-control" value="'''
                
    modsong3='''" readonly>
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Last played</label>
                <input type="text" name="newsonglastplayed" class="form-control" value="'''
                
    modsong4='''">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Last played</label>
                <input type="text" name="newsongkey" class="form-control" value="'''
    
    modsong5='''">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Last played</label>
                <input type="text" name="newsongkeydiff" class="form-control" value="'''
    
    modsong6='''">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Comments</label>
                <input type="text" name="newsongnotes" class="form-control" value="'''
    
    modsong7='''">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <label>Songsheet name (readonly)</label>
                <input type="text" name="songsheet" class="form-control" value="'''
    
    modsong8='''" readonly>
                <span class="help-block"></span>
            </div>
    '''

    modsong9='            <input type="hidden" name="password" value="' + masterpasswd + '">' 

    modsong10='''
            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="Next">
            </div>
        </form>
    </p>
</div>
'''

                
    modhtmlout=modsong1 + addsongapi + modsong2 + esong + modsong3 + elastplayed
    modhtmlout=modhtmlout + modsong4 + ekey + modsong5 + ekeydiff + modsong6 + enotes
    modhtmlout=modhtmlout + modsong7 + esongsheet + modsong8 + modsong9 + modsong10
    
    return modhtmlout
    
    

def lambda_handler(event, context):
    formparams = dict()
    try:
        htmlout=''
        form_data=str(event['body'])
        #this fails if the program is called with GET instead of POST with parameters.. 
        #hence the try
        
        #form comes through as base64 encoded.
        body_dec = base64.b64decode(form_data).decode('utf-8')
        form_list = str(body_dec).split("&")
        print(str(form_list))
    
        for pair in form_list:
            pairsplit=pair.split("=")
            nameitem=pairsplit[0]
            namevalue=pairsplit[1]
            formparams[nameitem] = namevalue
        
        password=formparams['password']
        formtype=formparams['formtype']
        
    except:
        form_data=""
        password=""
        formtype=""
    
    if ( password != masterpasswd ):
        html="wrong password"
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'text/html' },
            'body': html
        }

    if ( formtype == 'newsong'):
        html=''
        htmldebug=''
        #password is correct and we just exited from the login form. display summary.
        #songsheet=formparams['songsheet']
        print("newsong")
        #['formtype=newsong', 'newsongname=Holy+Forever', 'newsongsheetlink=today.pdf', 
        #'newsonglastplayed=2023-07', 'newsongkey=A', 'newsongkeydiff=%3F', 'newsongnotes=', 'filename=Way-maker-E.pdf', 'password=testing']
        newsongkey=urllib.parse.unquote_plus(formparams['newsongkey'])
        newsong=urllib.parse.unquote_plus(formparams['newsongname'])
        targetfilename = re.sub('[^a-zA-Z0-9 .]', '', newsong)
        targetfilename = targetfilename.replace(" ", "_")
        targetfilename = targetfilename + "_" + newsongkey + ".pdf"
        newsonglastplayed=formparams['newsonglastplayed']
        newsongkeydiff=urllib.parse.unquote_plus(formparams['newsongkeydiff'])
        newsongnotes=urllib.parse.unquote_plus(formparams['newsongnotes'])
        htmldebug = htmldebug + "newsong: " +  newsong + "<br>newsonglastplayed: " + newsonglastplayed
        htmldebug = htmldebug + "<br>newsongkey: " + newsongkey + "<br> newsongkeydiff: " + newsongkeydiff + "<br>newsongnotes: " + newsongnotes 
        htmldebug = htmldebug + "<br>targetfilename: " + targetfilename
        
        response = songtable.put_item(
        Item={
            'Song': newsong,
            'Lastplayed': newsonglastplayed,
            'Key': newsongkey,
            'Keydiff': newsongkeydiff,
            'Songsheet': targetfilename,
            'Notes': newsongnotes
            }
        )

        # 5242880 = 5mb
        form_data = s3_client.generate_presigned_post(
            Bucket= bucketname,
            Key= targetfilename,
            Conditions=[
                ["content-length-range", 10, max_file_size]
            ],
            ExpiresIn = 3600)
        
        htmlformdata=''
        print(form_data)
        for k, v in form_data['fields'].items():
            htmlformdata=htmlformdata + '             <input type="hidden" name="' + k + '" value="' + v + '" />\n'
        
        htmlfilesize="                <br><h4>&nbsp;&nbsp;Select file to upload (max " + str(float(max_file_size) / 1024) + " kb) </h4>"
        
        htmlend='''<br>
                &nbsp;&nbsp;<input type="file"   name="file" /> 
                <br><br>
                &nbsp&nbsp;<input type="submit" name="submit" value="Upload to object storage" />
            </form>
            
        '''
            
        html = htmlstart + formstart1 + htmlformdata + htmlfilesize + htmlend + songlistlogin1 + songlistapi + songlistlogin2 + masterpasswd + songlistlogin3 + htmldebug + '<br></html>'
    
    elif ( formtype == 'editsongform'):
        esong=urllib.parse.unquote_plus(formparams['song'])
        elastplayed=urllib.parse.unquote_plus(formparams['lastplayed'])
        ekey=urllib.parse.unquote_plus(formparams['key'])
        ekeydiff=urllib.parse.unquote_plus(formparams['keydiff'])
        esongsheet=formparams['songsheet']
        enotes=urllib.parse.unquote_plus(formparams['notes'])
        #html = htmlstart + "<br>song: " + esong + "<br>lastplayed: " + elastplayed + "<br>key: " + ekey + "<br>keydiff: " + ekeydiff + "<br>songsheet: " + esongsheet + "<br>notes: " + enotes
        htmledsong=editsong(esong, elastplayed, ekey, ekeydiff, esongsheet, enotes)
        html=htmlstart + htmledsong
        
    else:
        #html = htmlstart + str({textwrap.indent(input_fields, ' ' * 12)}) + htmlend
        #htmlpsk=displaypsk()
        html = htmlstart +  addsong1 + addsongapi + addsong2 + addsong3 + addsong4 

    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'text/html' },
        'body': html
    }
