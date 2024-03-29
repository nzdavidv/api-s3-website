import os
import json
from datetime import datetime, timezone, timedelta
from dateutil.tz import gettz
import boto3
import base64
import urllib.parse
from boto3.dynamodb.conditions import Key
from collections import OrderedDict

htmlbase=''
htmlend1=''
htmlend3=''

#two tables.. 'devnames' has friendly names for each mac address
#and 'temps' which has the temperature data.
dynamodb1 = boto3.resource('dynamodb')
devnamestable = dynamodb1.Table('devnames')
tempstable = dynamodb1.Table('temps')

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

#devicearray is used to store the mac address to name pairs.
devicearray = dict()

def displaysummary():
    #this function returns the summary information (this function is called with GET and no parameters)

    #html for the table
    localhtmlout='''
<table style="width:100%">
<tr>
<th>Device / Location</th>
<th>Last reading time</th>
<th>Temp</th>
<th>Humidity</th>
<th>Voltage</th>
<th>Graphs</th>
</tr>
'''

    #javascript for the form create and submit buttons
    javascr='''
<script>
    function formSubmit(devmac, dirdate, measure) {
        var form = document.createElement("form");
        var element1 = document.createElement("input"); 
        var element2 = document.createElement("input");
        var element3 = document.createElement("input");  

        form.method = "POST";
        form.action = "https://ifcf44wt0j.execute-api.us-east-1.amazonaws.com";   

        element1.value=devmac;
        element1.name="devmac";
        form.appendChild(element1);  

        element2.value=dirdate;
        element2.name="dirdate";
        form.appendChild(element2);

        element3.value=measure;
        element3.name="measure";
        form.appendChild(element3);
        document.body.appendChild(form);

        form.submit();
    }
</script>
'''

    #iterate on full table scan for devnamestable.. it's a small table with device and friendly names.
    response1 = devnamestable.scan()
    localhtmlout = localhtmlout + javascr
    for j in response1['Items']:
        macaddr=j['macaddr']
        devname=j['devname']

        #this has hard-coded in 12 hours adjustment from UTC for NZ which is probably a bad idea and
        #won't correct for daylight saving time. Fortunately i'm unlikely to want temp data at midnight.
        #so I don't really care. ..but yep, backlog to fix timezone.
        tnow = datetime.now(timezone.utc) + timedelta(hours=12)
        dirdate = tnow.strftime("%d-%m-%Y")
        #print("debug_dispSummary_dirdate: ", dirdate)
        
        #now the main temp query table for today (dirdate) for the device.
        response3 = tempstable.query(
            KeyConditionExpression='datestr = :datestr',
            FilterExpression='macaddr = :macaddr',
            ExpressionAttributeValues={
                ':datestr': dirdate,
                ':macaddr': macaddr
            }
        )
        # the purpose of the next part is to get the latest temp / humidity / battery reading.
        # there must be a better way but it works..
        devtemps = dict()
        devhum = dict()
        devbattery = dict()
        unixtimelabels = dict()
        for m in response3['Items']:
            temp=m['temp']
            humidity=m['humidity']
            battery=m['battery']
            unixtime=m['datetime']
            try:
                timelabel=m['timestr']
                # this is a 'try' because earlier version of the send-to-aws script didn't include
                # the timestr. I was going to work it out from 'datetime' unix epoch thing but
                # blurg.. too hard.
            except:
                timelabel=''
            devtemps[unixtime] = temp
            devhum[unixtime] = humidity
            devbattery[unixtime] = battery
            unixtimelabels[unixtime] = timelabel 
        sorteddevtemps = sorted(devtemps, reverse=True)
        for lasttime in sorteddevtemps:
            lasttemp=devtemps[lasttime]
            lasthum=devhum[lasttime]
            lastbattery=devbattery[lasttime]
            timelabel=unixtimelabels[lasttime]
            #print(str(pair),str(lasttemp))
            localhtmlout = localhtmlout + "<tr><td>" + devname + "</td><td>" + timelabel + "</td><td>" + str(lasttemp) + "</td><td>\n"
            localhtmlout = localhtmlout + str(lasthum) + "</td><td>" + str(lastbattery) + "</td><td>"
            bc='''<button onclick="formSubmit('''
            bd='''','temps')">'''
            be='''','humidity')">'''
            bf='''','battery')">'''
            localhtmlout = localhtmlout + bc + "'" + macaddr + "','" + dirdate + bd + " temps</button>"
            localhtmlout = localhtmlout + bc + "'" + macaddr + "','" + dirdate + be + " humidity</button>"
            localhtmlout = localhtmlout + bc + "'" + macaddr + "','" + dirdate + bf + " battery</button>"
            localhtmlout = localhtmlout + "</td></tr>\n"
            #the break means the loop around times stops after the first one.. giving only the latest time.
            break

    localhtmlout = localhtmlout + "</table>\n"
    return localhtmlout
    

def lambda_handler(event, context):
    #htmlbase below is the starting code for the temp/battery/humidity graph.
    htmlbase = ''' 
<!doctype html>
<html lang="en">
  <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load("current", {packages: ["line"]});
      google.charts.setOnLoadCallback(drawChart);

        function drawChart() {
          var data = new google.visualization.DataTable();
          data.addColumn('datetime', 'time of day');
          data.addColumn('number', 'temp');
          data.addRows([
'''

    htmlend1 = '''
  ]);

      var options = {
'''

    htmlend3 = '''
        };

      var chart = new google.charts.Line(document.getElementById('line_chart'));
      chart.draw(data, google.charts.Line.convertOptions(options));
}

    </script>
  </head>
  <body>
    <div id="line_chart" style=" height: 600px" ></div>

</body>
</html>
'''
    #print(event, "htmlbase ", htmlbase, "htmlend1 ", htmlend1, "htmlend3 ", htmlend3)
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
        #list1 = ["formtype=newuser",devmac=A4:C1:38:CF:53:B0&dirdate=2024-01-13&measure=temp
        for pair in form_list:
            pairsplit=pair.split("=")
            nameitem=pairsplit[0]
            namevalue=pairsplit[1]
            formparams[nameitem] = namevalue
        devmac=urllib.parse.unquote(formparams['devmac'])
        dirdate=formparams['dirdate']
        measure=formparams['measure']

    except:
        #if getting the form params failed then display a summary page.
        measure='summary'
        dirdate=''
        devmac=''
        htmlout=displaysummary()

    #if dirdate == "":
    #    tnow = datetime.now(gettz("UTC"))
    #    dirdate = tnow.strftime("%d-%m-%Y")
        
    print('devmac ', devmac) 
    print('dirdate ', dirdate)  
    print('measure ', measure)

    response4 = devnamestable.scan()
    for j in response4['Items']:
        macaddr=j['macaddr']
        devname=j['devname']
        devicearray[macaddr]=devname
        
    # for temps & humidity make a daily graph
    if measure == "temps" or measure == "humidity":
        htmlend2 = "       title: ' " + measure + " in " + devicearray[devmac] + " " + devmac + " for " + dirdate + "'"
        response5 = tempstable.query(
            KeyConditionExpression='datestr = :datestr',
            FilterExpression='macaddr = :macaddr',
            ExpressionAttributeValues={
                ':datestr': dirdate,
                ':macaddr': devmac
            }
        )
        #print("debug_devmac: ", devmac)
        for k in response5['Items']:
            if measure == "temps":
                value=k['temp']
            if measure == "humidity":
                value=k['humidity']
            ddmacaddr=k['macaddr']
            datedisp=k['datestr']
            dyear=datedisp.split('-')[2]
            dmonth=datedisp.split('-')[1]
            dday=datedisp.split('-')[0]
            #      [new Date(2024, 01, 13, 00, 00, 0), 26],
            graphdate="      [new Date(" + str(dyear) + ", "  + str(dmonth) + ", " + str(dday) + ", "
            try:
                timedisp=k['timestr']
                dhour=timedisp.split(':')[0]
                dmin=timedisp.split(':')[1]
                dsec=timedisp.split(':')[2]
                graphtime=str(dhour) + ", " + str(dmin) + ", " + str(dsec) + "), " 
                htmlout=htmlout + graphdate + graphtime + str(value) + "],\n"
            except:
                timedisp=''
            
            #print("debug_devmac: ", ddmacaddr)
    
    if measure == "battery":
        #for battery graph we want the last 5 days.
        htmlend2 = "       title: ' " + measure + " in " + devicearray[devmac] + " " + devmac + "'"
        daysago=-5
        #iterate through each of the last 5 days.
        while daysago < 0:
            xdaysago = datetime.now(timezone.utc) + timedelta(days=daysago)
            dirdate = xdaysago.strftime("%d-%m-%Y")
            response7 = tempstable.query(
                KeyConditionExpression='datestr = :datestr',
                FilterExpression='macaddr = :macaddr',
                ExpressionAttributeValues={
                    ':datestr': dirdate,
                    ':macaddr': devmac
                }
            )
            #print("debug_devmac: ", devmac)
            for k in response7['Items']:
                value=k['battery']
                ddmacaddr=k['macaddr']
                #"datestr": { "S": "13-01-2024"
                #"timestr": { "S": "18:00:33"
                datedisp=k['datestr']
                dyear=datedisp.split('-')[2]
                dmonth=datedisp.split('-')[1]
                dday=datedisp.split('-')[0]
                #      [new Date(2024, 01, 13, 00, 00, 0), 26],
                graphdate="      [new Date(" + str(dyear) + ", "  + str(dmonth) + ", " + str(dday) + ", "
                try:
                    timedisp=k['timestr']
                    dhour=timedisp.split(':')[0]
                    dmin=timedisp.split(':')[1]
                    dsec=timedisp.split(':')[2]
                    graphtime=str(dhour) + ", " + str(dmin) + ", " + str(dsec) + "), " 
                    htmlout=htmlout + graphdate + graphtime + str(value) + "],\n"
                except:
                    timedisp=''
            daysago += 1
        
    if measure == "summary":
        #htmlbase to make the summary page not-ugly
        htmlbase = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IOT stuff</title>
<meta content="width=device-width, initial-scale=1.0" name="viewport">
<meta content="Free Website Template" name="keywords">
<meta content="Free Website Template" name="description">

<link href="https://fonts.googleapis.com/css2?family=Open+Sans:300;400;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.10.0/css/all.min.css" rel="stylesheet">
<link href="https://nzvink-public.s3.amazonaws.com/style.css" rel="stylesheet">
</head>
<body>
    <body>
        <div class="wrapper">
            <div class="sidebar">
                <div class="sidebar-text d-flex flex-column h-100 justify-content-center text-center">
                    <img class="mx-auto d-block w-75 bg-primary img-fluid rounded-circle mb-4 p-3" src="https://uxwing.com/wp-content/themes/uxwing/download/internet-network-technology/iot-icon.png" alt="Image">
                    <h1 class="font-weight-bold">IoT</h1>
                    <p class="mb-4">
                        Home IoT sensors
                    </p>
                    <div class="d-flex justify-content-center mb-5">
                        <a class="btn btn-outline-primary mr-2" href="https://twitter.com/awscloud"><i class="fab fa-twitter"></i></a>
                        <a class="btn btn-outline-primary mr-2" href="https://www.facebook.com/groups/ToyotaMR2Spyder/"><i class="fab fa-facebook-f"></i></a>
                        <a class="btn btn-outline-primary mr-2" href="https://www.linkedin.com/"><i class="fab fa-linkedin-in"></i></a>
                        <a class="btn btn-outline-primary mr-2" href="https://github.com/"><i class="fab fa-github"></i></a>
                    </div>
                <div>    
                    <h4 class="mb-3 font-weight-bold">welcome</h4>
                </div>
                    <a class="btn btn-lg btn-block btn-primary mt-auto">IoT Temperatures</a>
                </div>
                <div class="sidebar-icon d-flex flex-column h-100 justify-content-center text-right">
                    <i class="fas fa-2x fa-angle-double-right text-primary"></i>
                </div>
            </div>
            <div class="content">
                <!-- Navbar Start -->
                <div class="container p-0">
'''
        htmlend1 = '''
                </div>

               
            </div>
        </div>
        
        <!-- Back to Top -->
        <a href="#" class="back-to-top"><i class="fa fa-angle-double-up"></i></a>
        
        <!-- JavaScript Libraries -->
        <script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.bundle.min.js"></script>
        <script src="lib/easing/easing.min.js"></script>
        <script src="lib/waypoints/waypoints.min.js"></script>

        <!-- Template Javascript -->
        <script src="js/main.js"></script>
    </body>
</html>
'''
        htmlend2 = ''
        htmlend3 = ''
        
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": htmlbase + htmlout + htmlend1 + htmlend2 + htmlend3
    }
