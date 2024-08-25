import os
import json
import boto3
import urllib.parse
import logging
import time
from botocore.exceptions import ClientError
from urllib.parse import unquote

sns = boto3.resource("sns")

def publish_message(topic, message, attributes):
        """
        Publishes a message, with attributes, to a topic. Subscriptions can be filtered
        based on message attributes so that a subscription receives messages only
        when specified attributes are present.

        :param topic: The topic to publish to.
        :param message: The message to publish.
        :param attributes: The key-value attributes to attach to the message. Values
                           must be either `str` or `bytes`.
        :return: The ID of the message.
        """
        try:
            att_dict = {}
            for key, value in attributes.items():
                if isinstance(value, str):
                    att_dict[key] = {'DataType': 'String', 'StringValue': value}
                elif isinstance(value, bytes):
                    att_dict[key] = {'DataType': 'Binary', 'BinaryValue': value}
            response = topic.publish(Message=message, MessageAttributes=att_dict)
            message_id = response['MessageId']
            print("Published message with attributes %s to topic %s.", attributes,
                 topic.arn)
        except ClientError:
            print("Couldn't publish message to topic %s.", topic.arn)
            raise
        else:
            return message_id



def lambda_handler(event, context):
    print(event)
    #first split the params passed in the form. 
    #going to turn the pairs into macnames
    formparams = dict()

    form_data=str(event['body'])
    form_list = form_data.split("&")
   
    for pair in form_list:
        pairsplit=pair.split("=")
        nameitem=pairsplit[0]
        namevalue=pairsplit[1]
        formparams[nameitem] = namevalue
    
    snsmessage="new webform contact\n"
    for p in formparams:
        #val=formparams[p]
        val=urllib.parse.unquote_plus(formparams[p])
        snsmessage=snsmessage + p + " " + val + "\n"
        
    emailTopic=sns.Topic(arn="arn:aws:sns:us-east-1:392495242865:emailNotify")
    publish_message(emailTopic, snsmessage, formparams)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": "thanks, your message has been sent"
    }
