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

#read the config file
config = configparser.ConfigParser()
config.read("nest.config")

# your nest api token
token = config['DEFAULT']['token']

#email to send alerts to
email = config['DEFAULT']['email']

#smtp (sendmail) configuration
smtp = config['DEFAULT']['smtp']
smtp_port = int(config['DEFAULT']['smtp_port'])

# maximum relative humidity; greater than this will trigger an email if email is set.
max_rh = int(config['DEFAULT']['max_rh'])

#connect to the Nest API to get current status of each thermostat in account
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

    print (device_name_long +":")

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

    messageText = "\n\r Humidity at {} is currently at {}%RH and {}F.\n\r System status is {} and target temp is " .format(device_name_long,humidity,ambient_temperature_f,hvac_state)

    if(hvac_mode == "heat-cool"):
        target_temperature_f = thermostat['target_temperature_high_f']
        #target temp is a range
        messageText += "{}F-{}F. \n\r ".format(thermostat['target_temperature_low_f'],target_temperature_f)
    else:
        messageText += "{}F. \n\r".format(target_temperature_f)

    if (int(humidity) > max_rh) and ( hvac_state == "off"):

        messageText += ("# WARNING: Humidity at {} is above {}%RH. \n\r").format(device_name_long,max_rh)

        if(email):
            email_alert(messageText)
            print("sent email.")

    else:
         messageText += "Humidity at {} is within range. ( <= {}%RH.) \n\r".format(device_name_long,max_rh)

    print(messageText)

print("run time:", time.perf_counter() - start_time, "sec")
