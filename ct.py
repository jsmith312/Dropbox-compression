#!/usr/bin/env python2.7

# import supporting modules for our compression
# program
import gzip
import dropbox
import boto.sqs
import urllib3
from boto.sqs.message import Message
import ConfigParser

# open our settings.cfg file and read in 
# credentials for connecting to our dropbox and AWS
# services
config = ConfigParser.RawConfigParser()
config.read("settings.cfg")
token = config.get('Dropbox', 'token')
sqs_id =  config.get('AWS', 'aws_access_key_id')
sqs_secret = config.get('AWS', 'aws_secret_access_key')
sqs_queue = config.get('AWS', 'queue')
sqs_region = config.get('AWS', 'region')

# connect to our SQS instance
conn = boto.sqs.connect_to_region(sqs_region, 
        aws_access_key_id=sqs_id,
        aws_secret_access_key=sqs_secret)

# while running the program will listen for a message from the 
# DPT 
while True:
    # create a new queue
    q = conn.create_queue(sqs_queue, 10) # 10-second message visibility
    # create our client token variable
    client = dropbox.client.DropboxClient(token)
    # read from the queue and place results in m
    m = q.read(wait_time_seconds = 3) # wait up to 3 seconds for message
    # if there is no message, then print NO MESSAGE
    if m is None:
        print "NO MESSAGE"
    # if there is a message, get our message body 
    # (which is the file path) and it is not the cursor, 
    # begin the compression process
    elif m.get_body != '/.cursor':
        # assign our message to a variable 
        dropboxName = m.get_body()
        # print the name of the file to the message stream
        print dropboxName
        # grab the name of the dropbox file
        dropfile = client.get_file(dropboxName)	
        # create a temp file to 
        tempfile = open('tempfile', 'wb')
        # zip up the file name
        compfile = gzip.GzipFile(m.get_body(), 'wb', fileobj=tempfile)
        # write to compfile
        compfile.writelines(dropfile)
        # close both files
        compfile.close()
        tempfile.close()
        # open tempfile and pass to put_file
        f = open("tempfile", 'rb')
        client.put_file(dropboxName+'.gz', f, overwrite=True)
        # delete our message
        q.delete_message(m)
