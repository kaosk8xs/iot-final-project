#!/usr/bin/env python3

import base64
import configparser
from datetime import datetime
import json

import paho.mqtt.client as mqtt
import csv

from groups import group14

# Read in config file with MQTT details.
config = configparser.ConfigParser()
config.read("config.ini")

# MQTT broker details
broker_address = config["mqtt"]["broker"]
username = config["mqtt"]["username"]
password = config["mqtt"]["password"]
print("Broker address: {}".format(broker_address))
print("Username: {}".format(username))
print("Password: {}".format(password))

# create a csv file to store the data
with open('final_data.csv', mode='w') as data_file:
    data_writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    data_writer.writerow(['time', 'temperature', 'gateway_id'])

# MQTT topic to subscribe to. We subscribe to all uplink messages from the
# devices.
topic = "v3/+/devices/+/up"

decoders = {
    14: group14.decode,
}

# Callback when successfully connected to MQTT broker.
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")

    if rc != 0:
        print(" Error, result code: {}".format(rc))


# Callback function to handle incoming MQTT messages
def on_message(client, userdata, message):
    # Timestamp on reception.
    current_date = datetime.now()

    # Handle TTN packet format.
    message_str = message.payload.decode("utf-8")
    message_json = json.loads(message_str)
    encoded_payload = message_json["uplink_message"]["frm_payload"]
    raw_payload = base64.b64decode(encoded_payload)
    gateway_id = message_json["uplink_message"]["rx_metadata"][0]["gateway_ids"]["gateway_id"]
    devide_id = message_json["end_device_ids"]["device_id"]

    if len(raw_payload) == 0:
        # Nothing we can do with an empty payload.
        return

    # First byte should be the group number, remaining payload must be parsed.
    group_number = raw_payload[0]
    remaining_payload = raw_payload[1:]

    # See if we can decode this payload.
    if group_number in decoders:
        try:
            temperature = decoders[group_number](remaining_payload)
        except Exception as e:
            print("Failed to decode payload for Group {}".format(group_number))
            print("  payload: {}".format(remaining_payload))
            print("  exception: {}".format(e))
            return

        if temperature == None:
            print("Undecoded message from Group {}".format(group_number))
        else:
            print("{} temperature: {}".format(current_date.isoformat(), temperature))
            with open('final_data.csv', mode='a') as data_file:
                data_writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                data_writer.writerow([current_date.isoformat(), temperature, gateway_id])

    else:
        print("Received message with unknown group: {}".format(group_number))


# MQTT client setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

# Setup callbacks.
client.on_connect = on_connect
client.on_message = on_message

# Connect to broker.
client.username_pw_set(username, password)
client.tls_set()
client.connect(broker_address, 8883)

# Subscribe to the MQTT topic and start the MQTT client loop
client.subscribe(topic)
client.loop_forever()
