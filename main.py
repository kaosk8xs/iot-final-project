#!/usr/bin/env python3

import base64
import configparser
from datetime import datetime
import json

import paho.mqtt.client as mqtt
import csv
# import CoreLocation
import os
# import time

# from test import LocationFetcher

# # Initialize the LocationFetcher
# location_fetcher = LocationFetcher()

# # Get the current location
# current_location = location_fetcher.fetch_location()
# if current_location:
#     print(f"Current Latitude: {current_location[0]}, Current Longitude: {current_location[1]}")
# else:
#     print("Location could not be determined.")


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
if not os.path.exists('final_data.csv'):
    with open('final_data.csv', mode='w') as data_file:
        data_writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data_writer.writerow(['time', 'rx_latitude', 'rx_longitude', 'gateway_id', 'device_id', 'spreading_factor'])

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
    # coord = lm.location().coordinate()
    # location = lm.location()
    # print(lm.location().coordinate().latitude)
    # time.sleep(5)
    # Timestamp on reception.
    current_date = datetime.now()

    # Handle TTN packet format.
    message_str = message.payload.decode("utf-8")
    message_json = json.loads(message_str)
    encoded_payload = message_json["uplink_message"]["frm_payload"]
    raw_payload = base64.b64decode(encoded_payload)
    gateway_id = message_json["uplink_message"]["rx_metadata"][0]["gateway_ids"]["gateway_id"]
    device_id = message_json["end_device_ids"]["device_id"]
    spreading_factor = message_json["uplink_message"]["settings"]["data_rate"]["lora"]["spreading_factor"]
    # try:
    #     current_location = location_fetcher.fetch_location()
    #     latitude = current_location.latitude
    #     longitude = current_location.longitude
    # except:
    r_latitude = 0
    r_longitude = 0
    for i in range(len(message_json["uplink_message"]["rx_metadata"])):
        if gateway_id == 'eui-9cd47dfffe9e0450':
            r_latitude = message_json["uplink_message"]["rx_metadata"][i]["location"]["latitude"]
            r_longitude = message_json["uplink_message"]["rx_metadata"][i]["location"]["longitude"]
            gateway_id = message_json["uplink_message"]["rx_metadata"][i]["gateway_ids"]["gateway_id"]
            break
        try:
            r_latitude = message_json["uplink_message"]["rx_metadata"][i]["location"]["latitude"]
            r_longitude = message_json["uplink_message"]["rx_metadata"][i]["location"]["longitude"]
            gateway_id = message_json["uplink_message"]["rx_metadata"][i]["gateway_ids"]["gateway_id"]
        except:
            pass

    if len(raw_payload) == 0:
        # Nothing we can do with an empty payload.
        return

    # First byte should be the group number, remaining payload must be parsed.
    group_number = raw_payload[0]
    remaining_payload = raw_payload[1:]

    # See if we can decode this payload.
    if group_number in decoders:
        try:
            temperature = 5
        except Exception as e:
            print("Failed to decode payload for Group {}".format(group_number))
            print("  payload: {}".format(remaining_payload))
            print("  exception: {}".format(e))
            return

        if temperature == None:
            print("Undecoded message from Group {}".format(group_number))
        else:
            print("{} sf: {}".format(current_date.isoformat(), spreading_factor))
            with open('final_data.csv', mode='a') as data_file:
                data_writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                data_writer.writerow([current_date.isoformat(), r_latitude, r_longitude, gateway_id, device_id, spreading_factor])

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
