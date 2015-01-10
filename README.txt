Dropbox App-based service that automatically compresses files stored in Dropbox. Gzip compression is used so that the file can be uncompressed using gunzip. This service will is implemented using GAE, GAE Push Queues, AWS EC2, AWS SQS, and Dropbox App into three tiers:

Monitoring Tier - The Monitoring Tier (MT) is a GAE application that is responsible for monitoring the Dropbox contents and causing new or modified files to be compressed.  It does this by receiving  webhook notifications from Dropbox. It must implement both the GET and POST methods and it must also validate the webhook invocation. When a webhook notification is received the MT enqueues a message to the Delta Processing tier using a GAE push queue. This will cause the Delta Processing Tier to fetch the deltas from Dropbox and process them.

Delta Processing Tier - The Delta Processing Tier (DPT) is invoked when the MT enqueues a message in the GAE push queue. It is implemented in the same GAE application as the Monitoring tier. The DPT must validate that the invocation is from the GAE Push Queue

Compression Tier - The Compression Tier (CT) receives messages from an AWS SQS queue. It runs in an EC2 instance. Each message contains the name of a file to be compressed. In response to receiving a message the CT reads the indicated file and produces a compressed version of the file. The compressed version is in gzip format and is produced using the Python gzip module. The name of the compressed file is the name of the uncompressed file with the suffix “.gz” (e.g. foo.txt becomes foo.txt.gz)

Keys to the dropbox and SQS connections are kept in a settings.cfg file and are obtained with the configParser

My settings.cfg file has the following format: 

[Dropbox]
token: <token>
secret: <secret>

[AWS]
aws_access_key_id = <key_id>
aws_secret_access_key = <access_key>
region = <instance_region>
queue = <some_queue>

where the region has to be us-west-1. 

Modules/libraries installed
------------------------
* /boto - boto library for connecting to SQS 
* /dropbox - dropbox library for connecting to dropbox app
* /flask - used for webhooks and app.route()
* /urllib3 - url library
* /werkzeug - werkzeug library
