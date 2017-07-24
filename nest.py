import http.client
from urllib.parse import urlparse
import json
import time
from datetime import datetime
import configparser

start_time = time.clock()

config = configparser.ConfigParser()   
config.read("nest.config")

token = config['DEFAULT']['token']

conn = http.client.HTTPSConnection("developer-api.nest.com")
headers = {'authorization': "Bearer {0}".format(token)}
conn.request("GET", "/", headers=headers)
response = conn.getresponse()

if response.status == 307:
    redirectLocation = urlparse(response.getheader("location"))
    conn = http.client.HTTPSConnection(redirectLocation.netloc)
    conn.request("GET", "/", headers=headers)
    response = conn.getresponse()
    if response.status != 200:
        raise Exception("Redirect with non 200 response")

data = response.read()
#print(data.decode("utf-8"))
parsed_json = json.loads(data)

devices = parsed_json['devices']
thermostats = devices['thermostats']

for deviceID, thermostat in thermostats.items():

	device_name_long = thermostat['name_long']
	filename = device_name_long + ".log"

	#print(deviceID, 'corresponds to', device_name_long)
	#for thermostatDataKey, thermostatData in thermostat.items():
		#print(device_name_long, " ", thermostatDataKey, ': ', thermostatData)

	humidity = thermostat['humidity']
	hvac_state = thermostat['hvac_state']
	hvac_mode = thermostat['hvac_mode']
	target_temperature_f = thermostat['target_temperature_f']
	ambient_temperature_f = thermostat['ambient_temperature_f']
	fan_timer_active = thermostat['fan_timer_active']

	timeStr = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	with open(filename, "a") as f:
		f.write('{}\t{}\t{}\t{}\t{}\t{}\r'.format(timeStr,ambient_temperature_f,humidity,hvac_state,target_temperature_f,fan_timer_active))


print("run time:", time.clock() - start_time, "sec")




