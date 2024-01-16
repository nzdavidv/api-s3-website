#!/bin/bash

basedir=/home/www
TMPDIR=$basedir/tmp
if [ ! -d $TMPDIR ]; then mkdir $TMPDIR ; fi
AWSFILE=$TMPDIR/aws-infile2.json

macaddr=$1
temp=$2
humidity=$3
battery=$4

if [ "$macaddr" == "" ] || [ "$temp" == "" ] || [ "$humidity" = "" ] || [ "$battery" == "" ]; then
 echo "usage: $0 mac temp humidity battery"
 exit 1
fi

 datenow=`date "+%Y%m%d %H:%M"`
 datestr=`date "+%d-%m-%Y"`
 timestr=`date "+%H:%M:%S"`
 unixdate=`date "+%s"`
 datesh=`echo "$datenow"|awk '{print $1}'`
 timesh=`echo "$datenow"|awk '{print $2}'`

#{
#    "datestr": {
#      "S": "03-09-2022"
#    },
#    "macdatetime": {
#      "S": "70:91:8F:9A:D2:63-1662138901"
#    },
#    "datetime": {
#      "N": "1662138901"
#    },
#    "temp": {
#      "N": "72"
#    },
#    "humidity": {
#      "N": "0"
#    },
#    "battery": {
#      "N": "80"
#    },
#    "macaddr": {
#      "S": "70:91:8F:9A:D2:63"
#    }
#}


 echo -e "{\n\t\"datestr\": {\"S\": \"${datestr}\"}," > $AWSFILE
 echo -e "\t\"timestr\": {\"S\": \"${timestr}\"}," >> $AWSFILE
 echo -e "\t\"macdatetime\": {\"S\": \"${macaddr}-${unixdate}\"}," >> $AWSFILE
 echo -e "\t\"datetime\": {\"N\": \"${unixdate}\"}," >> $AWSFILE
 echo -e "\t\"temp\": {\"N\": \"${temp}\"}," >> $AWSFILE
 echo -e "\t\"humidity\": {\"N\": \"${humidity}\"}," >> $AWSFILE
 echo -e "\t\"battery\": {\"N\": \"${battery}\"}," >> $AWSFILE
 echo -e "\t\"macaddr\": {\"S\": \"${macaddr}\"}\n}" >> $AWSFILE

 aws dynamodb put-item --table-name temps --item file://${AWSFILE}
