
#############LIBRERIAS######################################
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json
import RPi.GPIO as GPIO
############################################################


#############CONFIGURACION DE PINES DOMOTICA################
pin=7  
GPIO.setmode(GPIO.BOARD) 
GPIO.setup(pin, GPIO.OUT) 
channel = 40
# Receive input signals through the pin.
GPIO.setup(channel, GPIO.IN)
############################################################

#############CERTIFICADOS RASPBERRY PI######################
# A random programmatic shadow client ID.
SHADOW_CLIENT = "Raspberry_AYC"
# The unique hostname that &IoT; generated for
# this device.
HOST_NAME = "a3n2wuzb1tavdy-ats.iot.us-east-2.amazonaws.com"
# The relative path to the correct root CA file for &IoT;,
# which you have already saved onto this device.
ROOT_CA = "Amazon_Root_CA_2.pem"
# The relative path to your private key file that
# &IoT; generated for this device, which you
# have already saved onto this device.
PRIVATE_KEY = "f103bf699c-private.pem.key"
# The relative path to your certificate file that
# &IoT; generated for this device, which you
# have already saved onto this device.
CERT_FILE = "f103bf699c-certificate.pem.crt"
# A programmatic shadow handler name prefix.
SHADOW_HANDLER = "Raspberry_AYC"
# Automatically called whenever the shadow is updated.


AllowedActions = ['both', 'publish', 'subscribe']

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    if (message.payload=="ON"):
	GPIO.output(pin,GPIO.HIGH) 
    	time.sleep(5)
    else:
	GPIO.output(pin,GPIO.LOW)
    print("--------------\n\n")


# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="OFF",
                    help="Message to publish")

args = parser.parse_args()
#host = args.host
host=HOST_NAME
#rootCAPath = args.rootCAPath
rootCAPath=ROOT_CA
#certificatePath = args.certificatePath
certificatePath="f103bf699c-certificate.pem.crt"
#privateKeyPath = args.privateKeyPath
privateKeyPath=PRIVATE_KEY
#port = args.port
port =8883
#useWebsocket = args.useWebsocket
useWebsocket=False
#clientId = args.clientId
clientId="basicPubSub"
#topic = args.topic
topic="sdk/test/Python"

############################################################

# Configure logging

#logger = logging.getLogger("AWSIoTPythonSDK.core")
#logger.setLevel(logging.DEBUG)
#streamHandler = logging.StreamHandler()
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#streamHandler.setFormatter(formatter)
#logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

def myShadowUpdateCallback(payload, responseStatus, token):
	print()
	print('UPDATE: $aws/things/' + SHADOW_HANDLER +
	'/shadow/update/#')
	print("payload = " + payload)
	print("responseStatus = " + responseStatus)
	print("token = " + token)
# Create, configure, and connect a shadow client.
myShadowClient = AWSIoTMQTTShadowClient(SHADOW_CLIENT)
myShadowClient.configureEndpoint(HOST_NAME, 8883)
myShadowClient.configureCredentials(ROOT_CA, PRIVATE_KEY,
CERT_FILE)
myShadowClient.configureConnectDisconnectTimeout(10)
myShadowClient.configureMQTTOperationTimeout(5)
myShadowClient.connect()
# Create a programmatic representation of the shadow.
myDeviceShadow = myShadowClient.createShadowHandlerWithName(
SHADOW_HANDLER, True)


#############ENVIAR NOTIFICACION POR CORREO#################
# Publish to the same topic in a loop
loopCount = 0
for i in range (0,10):
    if args.mode == 'both' or args.mode == 'publish':
        message = {}
        message['message'] = args.message
        message['sequence'] = loopCount
        messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish(topic, messageJson, 1)
        if args.mode == 'publish':
            print('Published topic %s: %s\n' % (topic, messageJson))
        loopCount += 1
		
	if GPIO.input(channel):
		myDeviceShadow.shadowUpdate(
		'{"state":{"reported":{"voltaje":"Okay"}}}',
		myShadowUpdateCallback, 5)
	else:
		myDeviceShadow.shadowUpdate(
		'{"state":{"reported":{"voltaje":"low"}}}',
		myShadowUpdateCallback, 5)
    time.sleep(5)
############################################################
