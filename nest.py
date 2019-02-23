#use python 3
import http.client
from urllib.parse import urlparse
import json
import time
from datetime import datetime
import configparser
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def email_alert(messageText):
    s = smtplib.SMTP(host=smtp, port=smtp_port)

    msg = MIMEMultipart()       # create a message

    # setup the parameters of the message
    msg['From']=email
    msg['To']=email
    msg['Subject']="NestLogger alert"

    # add in the message body
    msg.attach(MIMEText(messageText, 'plain'))

    # send the message via the server set up earlier.
    s.send_message(msg)

    del msg
    return


start_time = time.perf_counter()

config = configparser.ConfigParser()
config.read("nest.config")

token = config['DEFAULT']['token']
email = config['DEFAULT']['email']
smtp = config['DEFAULT']['smtp']
smtp_port = int(config['DEFAULT']['smtp_port'])
max_rh = int(config['DEFAULT']['max_rh'])
#maximum relative humidity; greater than this will trigger an email if email is set.

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

    if(hvac_mode == "heat-cool"):
        target_temperature_f = thermostat['target_temperature_high_f']


    if (int(humidity) > max_rh) and ( hvac_state == "off"):
        if(email):
            if(hvac_mode == "heat-cool"):
                email_alert("Humidity at {} is above {}%RH. It is currently at {}%RH and {}F.\r System status is {} and target temp is {}F-{}F.".format(device_name_long,max_rh,humidity,ambient_temperature_f,hvac_state,thermostat['target_temperature_low_f'],target_temperature_f))
            else:
                email_alert("Humidity at {} is above {}%RH. It is currently at {}%RH and {}F.\r System status is {} and target temp is {}F.".format(device_name_long,max_rh,humidity,ambient_temperature_f,hvac_state,target_temperature_f))

            print("sent email.")



print("run time:", time.perf_counter() - start_time, "sec")
