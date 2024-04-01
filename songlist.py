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

s3 = boto3.resource('s3')
bucketname = os.environ['BUCKETNAME']
bucket = s3.Bucket(bucketname)
addsongapi = os.environ['ADDSONGAPI']
songlistapi = os.environ['SONGLISTAPI']
masterpasswd = os.environ['MPASSWD']
dbname = os.environ['DATABASE']

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
        
htmlstart='''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <style type="text/css">
        body{ font: 14px sans-serif; }
        .wrapper{ width: 350px; padding: 20px; }
        .collapsible {
          color: black;
          cursor: pointer;
          padding: 10px;
          width: 30px;
          border: none;
          text-align: left;
          outline: none;
          font-size: 15px;
        }
        .active, .collapsible:hover {
          background-color: #555;
        }
        .content {
          padding: 0 18px;
          display: none;
          overflow: hidden;
          background-color: #f1f1f1;
        }
</style>
</head>
<body>
'''

htmllogin1='''
    <div class="wrapper">
        <h2>Login</h2>
        <p>Please fill in your credentials to login.</p>
        <form action="'''

htmllogin2='''"method="post">
            <input type="hidden" name="formtype" value="login">
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" class="form-control">
                <span class="help-block"></span>
            </div>
            <div class="form-group">
                <input type="submit" class="btn btn-primary" value="Login">
            </div>
        </form>
    </div>
</body>
</html>
'''

htmlend='''
</body>
</html>
'''

addsong1='''
<script>
    function formSubmit2(password) {
        var form = document.createElement("form");
        var element1 = document.createElement("input");
        element1.setAttribute("type", "hidden");
        var element2 = document.createElement("input");
        element2.setAttribute("type", "hidden");

        form.method = "POST";
        form.action = "'''

addsong2='''";
        element1.value=password;
        element1.name="password";
        form.appendChild(element1);  
        
        element2.value="newsongform";
        element2.name="formtype";
        form.appendChild(element2);

        document.body.appendChild(form);

        form.submit();
    }
</script>

            <button onclick="formSubmit2('''

addsong3=''')"style="float: right; margin-right: 100px;">Add song</button>
'''

def editsong(esong, elastplayed, ekey, ekeydiff, esongsheet, enotes, eformnumber):
    #   song=j['Song']
    #   lastplayed=j['Lastplayed']
    #   key=j['Key']
    #   keydiff=j['Keydiff']
    #   songsheet=j['Songsheet']
    #   notes=j['Notes']
    
    editsong1='''(password, song, lastplayed, key, keydiff, songsheet, notes ) {
     var form = document.createElement("form");
     var element1 = document.createElement("input");
     element1.setAttribute("type", "hidden");
     var element2 = document.createElement("input");
     element2.setAttribute("type", "hidden");
     var element3 = document.createElement("input");
     element3.setAttribute("type", "hidden");
     var element4 = document.createElement("input");
     element4.setAttribute("type", "hidden");
     var element5 = document.createElement("input");
     element5.setAttribute("type", "hidden");
     var element6 = document.createElement("input");
     element6.setAttribute("type", "hidden");
     var element7 = document.createElement("input");
     element7.setAttribute("type", "hidden");
     var element8 = document.createElement("input");
     element8.setAttribute("type", "hidden");
    
     form.method = "POST";
     form.action = "'''

    editsong2='''
     document.body.appendChild(form);
     form.submit();
    }
</script>

            <button onclick="formSubmit'''

    editsong3=''')"style="float: right; margin-right: 100px;">Edit</button>
'''

    editsongout="<script>\n function formSubmit" + str(eformnumber) + editsong1 + addsongapi + '" \n'
    editsongout= editsongout + '      element1.value="' + masterpasswd + '"\n      element1.name="password"; \n     form.appendChild(element1); \n'
    editsongout= editsongout + '      element2.value="' + esong + '"\n     element2.name="song"; \n     form.appendChild(element2); \n'
    editsongout= editsongout + '      element3.value="' + elastplayed + '"\n     element3.name="lastplayed"; \n     form.appendChild(element3); \n'
    editsongout= editsongout + '      element4.value="' + ekey + '"\n     element4.name="key"; \n     form.appendChild(element4); \n'
    editsongout= editsongout + '      element5.value="' + ekeydiff + '"\n     element5.name="keydiff"; \n     form.appendChild(element5); \n'
    editsongout= editsongout + '      element6.value="' + esongsheet + '"\n     element6.name="songsheet"; \n     form.appendChild(element6); \n'
    editsongout= editsongout + '      element7.value="' + enotes + '"\n     element7.name="notes"; \n     form.appendChild(element7); \n'
    editsongout= editsongout + '      element8.value="editsongform"\n     element8.name="formtype"; \n     form.appendChild(element8); \n'
    editsongout= editsongout + editsong2 + str(eformnumber) + "(" + editsong3
    
    return editsongout
        
def displaysummary(order):
    formnumber=3
    #this function returns the summary information (this function is called with GET and no parameters)

    #javascript for the form create and submit buttons
    javascr1='''
    <script>
    function formSubmit(password, songsheet, formtype) {
        var form = document.createElement("form");
        var element1 = document.createElement("input");
        element1.setAttribute("type", "hidden");
        var element2 = document.createElement("input");
        element2.setAttribute("type", "hidden");
        var element3 = document.createElement("input");
        element3.setAttribute("type", "hidden");

        form.method = "POST";
        form.action = "'''
    
    javascr2='''"
        element1.value=password;
        element1.name="password";
        form.appendChild(element1);  

        element2.value=songsheet;
        element2.name="songsheet";
        form.appendChild(element2);
        
        element3.value=formtype;
        element3.name="formtype";
        form.appendChild(element3);
        document.body.appendChild(form);

        form.submit();
    }
    var coll = document.getElementsByClassName("collapsible");
    var i;
    
    for (i = 0; i < coll.length; i++) {
      coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "block") {
          content.style.display = "none";
        } else {
          content.style.display = "block";
        }
      });
    }
</script>
'''
    tablehead='''
<table style="width:90%" class="table table-striped">
'''

    #iterate on full table scan for items
    response1 = songtable.scan()
    
    localhtmlout = htmlstart + addsong1 + addsongapi + addsong2 + "'" + masterpasswd + "'" + addsong3 + javascr1 + songlistapi + javascr2
    localhtmlout = localhtmlout + tablehead
    
    bc='''<button onclick="formSubmit('''
    bfdate='''','bydate','login')">'''
    bfkey='''','bykey','login')">'''
    bfsong='''','bysong','login')">'''
 
    localhtmlout = localhtmlout + "<tr><td>&nbsp</td>"
    localhtmlout = localhtmlout + "<td>Song title &nbsp&nbsp" + bc + "'" + masterpasswd + bfsong + "sort</button></td>"
    localhtmlout = localhtmlout + "<td>Date last played &nbsp&nbsp" + bc + "'" + masterpasswd + bfdate + "sort</button></td>" 
    localhtmlout = localhtmlout + "<td>Key &nbsp&nbsp" + bc + "'" + masterpasswd + bfkey + "sort</button></td>"
    localhtmlout = localhtmlout + "<td>Key change from Spotify</td><td>Comments</td><td>&nbsp</td></tr>"

    songlistarray = []
    songid=0
    
    for j in response1['Items']:
        #Song: ${Song}\nLastplayed: ${Lastplayed}\nKey: ${Key}\nKeydiff: ${Keydiff}\nSongsheet: ${Songsheet}\nNotes: ${Notes}
        song=j['Song']
        lastplayed=j['Lastplayed']
        key=j['Key']
        keydiff=j['Keydiff']
        songsheet=j['Songsheet']
        notes=j['Notes']
        
        songlistarray.insert(songid, [song, lastplayed, key, keydiff, songsheet, notes])
        songid = songid + 1
    
    if ( order == "bydate" ):
        songlistarray.sort(key=lambda songlistarray: songlistarray[1])
    elif ( order == "bysong" ):
        songlistarray.sort(key=lambda songlistarray: songlistarray[0])
    elif ( order == "bykey" ):
        songlistarray.sort(key=lambda songlistarray: songlistarray[2])
    else:
        songlistarray.sort(key=lambda songlistarray: songlistarray[0])
    
    for sslist in songlistarray:
        ssid=0
        for sslistitem in sslist:
            if ( ssid == 0):
                song=sslistitem
                ssid=ssid + 1
            elif (ssid == 1):
                lastplayed=sslistitem
                ssid=ssid + 1
            elif (ssid == 2):
                key=sslistitem
                ssid=ssid + 1
            elif (ssid == 3):
                keydiff=sslistitem
                ssid=ssid + 1
            elif (ssid == 4):
                songsheet=sslistitem
                ssid=ssid + 1
            elif (ssid == 5):
                notes=sslistitem
                ssid=0

        be='''','fileget')">'''

        #editsong(esong, elastplayed, ekey, ekeydiff, esongsheet, enotes, eformnumber):
        formnumber = formnumber + 1
        editsonghtml = editsong(song, lastplayed, key, keydiff, songsheet, notes, formnumber)
        localhtmlout = localhtmlout + "<tr><td>" + bc + "'" + masterpasswd + "','" + songsheet + be + " songsheet</button>"
        localhtmlout = localhtmlout + "</td><td>" + song + "</td><td>" + lastplayed + "</td><td>" + key + "</td><td>" + keydiff + "</td><td>\n"
        localhtmlout = localhtmlout + notes + "</td><td>" + editsonghtml + "</td></tr>\n"
    
    localhtmlout = localhtmlout + "</table>" + htmlend
    
    return localhtmlout

html=''

def readhtmlfile(filename):
    filehand = s3.Object(bucketname,filename)
    body = filehand.get()['Body'].read()
    html=body.decode('utf8')
    return html
    
def readbinfile(filename):
    print ("readbinfile", bucketname, filename)
    s3obj = s3.Object(bucketname,filename)
    filehandle = s3obj.get()['Body'].read()
    filebytes = BytesIO(filehandle).getvalue()
    return filebytes

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
        filereq = event['rawPath']
        filereqn=filereq[1:]
        print ("filereqn", filereqn)

    if ( password != "" ) and ( password != masterpasswd ):
        html="wrong password"
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'text/html' },
            'body': html
        }

        
    if ( formtype == 'fileget'):
        songsheet=formparams['songsheet']
        print ("fileget:", songsheet)
        if ('.PDF' in songsheet) or ('.pdf' in songsheet):
            try:
                reads3out=readbinfile(songsheet) 
                html=reads3out
                return {
                    "statusCode": 200,
                    'headers': { 'Content-Type': 'application/pdf' },
                    'body': base64.b64encode(html),
                    'isBase64Encoded': True
                }
            except:
                html=songsheet + " failed to open"
                return {
                    "statusCode": 200,
                    'headers': { 'Content-Type': 'text/html' },
                    'body': html
                }
        elif ('.jpg' in songsheet) or ('.jpeg' in songsheet):
            reads3out=readbinfile(songsheet) 
            html=reads3out
            return {
                "statusCode": 200,
                'headers': { 'Content-Type': 'image/jpg' },
                'body': base64.b64encode(html),
                'isBase64Encoded': True
            }


    if ( formtype == 'login'):
        #password is correct and we just exited from the login form. display summary.
        try:
            songsheet=formparams['songsheet']
            if( songsheet == "bydate"):
                html=displaysummary("bydate")
            elif ( songsheet == "bykey"):
                html=displaysummary("bykey")
            else:
                html=displaysummary("bysong")
        except:
            html=displaysummary("bysong")
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'text/html' },
            'body': html
        }
    
    if (formtype == "") and ( filereqn == ""): 
        html=htmlstart + htmllogin1 + songlistapi + htmllogin2
        return {
            "statusCode": 200,
            'headers': { 'Content-Type': 'text/html' },
            'body': html
        }
