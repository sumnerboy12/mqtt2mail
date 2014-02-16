**NOTE: this script has been superceeded by [mqttwarn](https://github.com/jpmens/mqttwarn).**
---

## mqtt2mail

This program subscribes to any number of MQTT topics (including wildcards) and publishes received payloads as email messages (copy `mqtt2mail.conf.sample` to `mqtt2mail.conf` for use). 

See details in the config sample for how to configure this script.

## Requirements

* An MQTT broker (e.g. [Mosquitto](http://mosquitto.org))
* Email address and authentication details
* The Paho Python module: `pip install paho-mqtt`

