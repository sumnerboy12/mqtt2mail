#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
import paho.mqtt.client as paho   # pip install paho-mqtt
import logging
import os
import signal
import sys
import time

__author__    = 'Ben Jones <ben.jones12()gmail.com>'
__copyright__ = 'Copyright 2013 Ben Jones'
__license__   = """Eclipse Public License - v 1.0 (http://www.eclipse.org/legal/epl-v10.html)"""

# script name used for conf/log file names etc
SCRIPTNAME = 'mqtt2mail'

# get the config and log file names
CONFIGFILE = os.getenv(SCRIPTNAME.upper() + 'CONF', SCRIPTNAME + ".conf")
LOGFILE = os.getenv(SCRIPTNAME.upper() + 'LOG', SCRIPTNAME + ".log")

# load configuration
conf = {}
try:
    execfile(CONFIGFILE, conf)
except Exception, e:
    print "Cannot load configuration %s: %s" % (CONFIGFILE, str(e))
    sys.exit(2)

LOGLEVEL = conf.get('loglevel', logging.DEBUG)
LOGFORMAT = conf.get('logformat', '%(asctime)-15s %(message)s')

MQTT_HOST = conf.get('broker', 'localhost')
MQTT_PORT = int(conf.get('port', 1883))
MQTT_LWT = conf.get('lwt', None)

# initialise logging    
logging.basicConfig(filename=LOGFILE, level=LOGLEVEL, format=LOGFORMAT)
logging.info("Starting " + SCRIPTNAME)
logging.info("INFO MODE")
logging.debug("DEBUG MODE")

# initialise MQTT broker connection
mqttc = paho.Client(SCRIPTNAME, clean_session=False)

# check for authentication
if conf['username'] is not None:
    mqttc.username_pw_set(conf['username'], conf['password'])

# configure the last-will-and-testament
if MQTT_LWT is not None:
    mqttc.will_set(MQTT_LWT, payload=SCRIPTNAME, qos=0, retain=False)

def connect():
    """
    Connect to the broker
    """
    logging.debug("Attempting connection to MQTT broker %s:%d..." % (MQTT_HOST, MQTT_PORT))
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_disconnect = on_disconnect

    result = mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
    if result == 0:
        mqttc.loop_forever()
    else:
        logging.info("Connection failed with error code %s. Retrying in 10s...", result)
        time.sleep(10)
        connect()
         
def disconnect(signum, frame):
    """
    Signal handler to ensure we disconnect cleanly 
    in the event of a SIGTERM or SIGINT.
    """
    logging.debug("Disconnecting from MQTT broker...")
    mqttc.loop_stop()
    mqttc.disconnect()
    logging.debug("Exiting on signal %d", signum)
    sys.exit(signum)

def send_mail(username, password, recipient, subject, body):
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (username, ", ".join(recipient), subject, body)
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')  
        server.ehlo()
        server.starttls()  
        server.ehlo()
        server.login(username,password)  
        server.sendmail(username, recipient, message)  
        server.close() 
    except Exception, e:
        print "mqtt2xbmc: ", str(e)

def on_connect(mosq, userdata, result_code):
    logging.debug("Connected to MQTT broker, subscribing to topics...")
    for topic in conf['topicsubject'].keys():
        logging.debug("Subscribing to %s" % topic)
        mqttc.subscribe(topic, 0)

def on_message(mosq, userdata, msg):
    """
    Message received from the broker
    """
    topic = msg.topic
    payload = str(msg.payload)
    logging.debug("Message received on %s: %s" % (topic, payload))

    username = conf['mailusername']
    password = conf['mailpassword']
    recipients = conf['recipient']
    subject = None

    # Try to find matching settings for this topic
    for sub in conf['topicsubject'].keys():
        if paho.topic_matches_sub(sub, topic):
            subject = conf['topicsubject'][sub]
            break
    
    if subject is None:
        return
        
    for recipient in recipients:
        logging.debug("Sending email to %s [%s]..." % (recipient, subject))
        send_mail(username, password, [recipient], subject, payload)

def on_disconnect(mosq, userdata, result_code):
    """
    Handle disconnections from the broker
    """
    if result_code == 0:
        logging.info("Clean disconnection")
    else:
        logging.info("Unexpected disconnection! Reconnecting in 5 seconds...")
        logging.debug("Result code: %s", result_code)
        time.sleep(5)
        connect()

# use the signal module to handle signals
signal.signal(signal.SIGTERM, disconnect)
signal.signal(signal.SIGINT, disconnect)
        
# connect to broker and start listening
connect()
