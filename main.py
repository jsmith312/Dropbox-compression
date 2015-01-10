#!/usr/bin/env python2.7
import time
import dropbox
import urllib3
import ConfigParser
import boto.sqs
from pprint import *
from flask import Flask, request, abort
from hashlib import sha256
import hmac
import threading
from google.appengine.api import taskqueue
from boto.sqs.message import Message

app = Flask(__name__)
app.config['DEBUG'] = True

# Config parser to read from the settings.cfg file which contains
# access tokens to the cloud provider software
config = ConfigParser.RawConfigParser()
config.read("settings.cfg")
# Dropbox
token = config.get('Dropbox', 'token')
APP_SECRET = config.get('Dropbox', 'secret')

# AWS
sqs_id =  config.get('AWS', 'aws_access_key_id')
sqs_secret = config.get('AWS', 'aws_secret_access_key')
sqs_queue = config.get('AWS', 'queue')
sqs_region = config.get('AWS', 'region')

# Connect to our AWS SQS region. Access key and id are located in
# settings.cfg file
conn = boto.sqs.connect_to_region(sqs_region, 
        aws_access_key_id=sqs_id,
        aws_secret_access_key=sqs_secret)

# handler for root url
@app.route('/')
def Frontend():
    return ''

# Respond to the webhook verification (GET request) 
# by echoing back the challenge parameter.
@app.route('/webhook', methods=['GET'])
def verify():
    return request.args.get('challenge')

# POST url to receive the task queue form and pass it 
# through the SQS to be printed
@app.route('/webhook', methods=['POST'])
def webhook():
    # Make sure this is a valid request from Dropbox
    signature = request.headers.get('X-Dropbox-Signature')
    if signature != hmac.new(APP_SECRET, request.data, sha256).hexdigest():
        abort(403)
    # grab current time
    curr_time = time.ctime()
    # feed to our task queue and redirect to the delta
    # processing tier
    taskqueue.add(url='/DPT', params={'time':curr_time})
    return ''

@app.route('/DPT', methods=['POST'])
def DeltaProcessTier():
    if request.headers.get('X-AppEngine-QueueName') is None:
        # Ignore if not from AppEngine
        abort(403)
    # flag variable to determine if we should write to our cursor
    writeCursor = False
    # set our client variable
    client = dropbox.client.DropboxClient(token)
    # if the /.cursor file exists, assign cursor to
    # contents of the file
    # if it doesnt exist, set cursor ro none
    try:
        f = client.get_file('/.cursor')
        cursor = f.read()
    except:
        cursor = None
    # assign our delta with the cursor
    delta = client.delta(cursor)
    # loop through metadat in delta entries and check,
    for path, metadata in delta['entries']:
        # check if the file is not deleted
        if metadata != None:
            # check if the file path is not /.cursor
            if path != '/.cursor':
                # check if it is not a directory
                if metadata['is_dir'] == False:
                    # check if it not an already compressed file
                    if path.endswith('.gz') == False:
                        # if we have reached this point, we know that 
                        # we can write to our cursor and send the file 
                        # name to the queue
                        # set writeCursor to True
                        writeCursor = True
                        # create the queue
                        q = conn.create_queue(sqs_queue, 10) 
                        # Create our message object that will hold 
                        # our message and pass it to the queue
                        m = Message()
                        # set the message to be the file name 
                        m.set_body(path)
                        # write the message to the queue
                        q.write(m)
    # set our new cursor
    cursor = delta['cursor']
    # if the writeCursor flag is true, put the /.cursor file
    # in the dropbox
    if writeCursor is True:
        client.put_file('/.cursor', cursor, overwrite=True)
    return ''









