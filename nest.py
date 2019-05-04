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

def email_alert(subjectText, messageText):
    s = smtplib.SMTP(host=smtp, port=smtp_port)

    msg = MIMEMultipart()       # create a message

    # setup the parameters of the message
    msg['From']=email
    msg['To']=email
    msg['Subject']="Nestools alert: "+ subjectText

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

# cool to dry settings.
cool_to_dry = bool(config['DEFAULT']['cool_to_dry'])
cool_to_dry_min_f = int(config['DEFAULT']['cool_to_dry_min_f'])


#connect to the Nest API to get current status of each thermostat in account
conn = http.client.HTTPSConnection("developer-api.nest.com")
headers = {'Authorization': "Bearer {0}".format(token)}
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

    #write log file line
    with open(filename, "a") as f:
        f.write('{}\t{}\t{}\t{}\t{}\t{}\n'.format(timeStr,ambient_temperature_f,humidity,hvac_state,target_temperature_f,fan_timer_active))

    messageText = "Humidity at {} is currently at {}%RH and {}F.\n System status is {} and target temp is " .format(device_name_long,humidity,ambient_temperature_f,hvac_state)

    if(hvac_mode == "heat-cool"):
        target_temperature_f = thermostat['target_temperature_high_f']
        #target temp is a range
        messageText += "{}F-{}F. \n ".format(thermostat['target_temperature_low_f'],target_temperature_f)
    else:
        messageText += "{}F. \n".format(target_temperature_f)

    #humidity alerts happen ONLY when the system is off
    if (int(humidity) > max_rh) and ( hvac_state == "off"):

        messageText += ("# WARNING: Humidity at {} is above {}%RH. \n").format(device_name_long,max_rh)

        #make sure cool to dry is on, and the current temp is greater than the minimum set in the config file
        if cool_to_dry:

            if ambient_temperature_f > cool_to_dry_min_f :
                # turn on and lower temp on thermostat to 1 degree below target
                if target_temperature_f >= ambient_temperature_f:
                    target_temperature_f = ambient_temperature_f - 1;

                    post_json = {}

                    if(hvac_mode == "heat-cool"):
                        if target_temperature_f >= thermostat['target_temperature_low_f']:
                            post_json = {"target_temperature_high_f": target_temperature_f}

                    else:
                        if(hvac_mode == "cool"):
                            post_json = {"target_temperature_f" : target_temperature_f}


                    if(post_json != {}):

                        print(("setting new target temp: {}F").format(target_temperature_f))

                        # post the new temperature
                        deviceURL = "/devices/thermostats/" + deviceID

                        conn2 = http.client.HTTPSConnection("developer-api.nest.com")

                        headers = {'Authorization': "Bearer {0}".format(token), 'Content-type': 'application/json'}

                        #print(json.dumps(post_json))
                        conn2.request("PUT", deviceURL, json.dumps(post_json), headers=headers)
                        response = conn2.getresponse()

                        if response.status == 307:
                            redirectLocation = urlparse(response.getheader("location"))
                            conn2 = http.client.HTTPSConnection(redirectLocation.netloc)
                            conn2.request("PUT", deviceURL, json.dumps(post_json), headers=headers)

                            response = conn2.getresponse()
                            if response.status != 200:
                                print(str(response.status) + response.read().decode() )
                                raise Exception("Redirect with non 200 response")

                        #messageText += str(response.code) + response.read().decode() + "\n"
                        messageText += ("Lowering thermostat to {}F.\n").format(target_temperature_f)



            if(email):
                email_alert(device_name_long, messageText)
                print("sent email.")

    #else:
         #messageText += "Humidity at {} is within range. ( <= {}%RH.) \n".format(device_name_long,max_rh)





    print(messageText)

print("run time:", time.perf_counter() - start_time, "sec")
