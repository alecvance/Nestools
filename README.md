This script is a template to start working with the Nest API and log data from your thermostats. It can also optionally email you an alert when the relative humidity is above a certain amount.*

It does not do any authentication; you will have to do that manually in order to get a token. 
The steps are generally outlined below. For specifics, see the Nest Developer site.

To get an access token:

1) Get a Nest Developer account.
2) Create and register a Nest app from your Nest Developer account and set privileges on your Nest app. 
3) Use OAUTH to setup and authorize your Nest device with the code.
4) Get the access token for your Nest account to connect to the app.

Once you have a token:

5) Rename sample.config to nest.config and put your access token in there.
6) Install Python 3 if necessary.
7) Run the script from a terminal: "python3 nest.py", or add to your crontab to run periodically. 

Each run will append to log file(s); there is a different log file for each thermostat.

The log files show the following per line in order:
	datetime, inside temperature, inside relative humidity, current state, target temperature.

Temperatures are in Fahrenheit, but can be changed to Celsius with little effort.

If wish to use the email alert system, enter your email address and smtp server and port. You may also wish to adjust the maximum  relative humidity  (max_rh) before alerts occur. 

* I created this script because our South Louisiana house traps humidity and Nest's "Cool to Dry" feature will not activate if the temperature is less than 75-80 degrees. If Nest engineers lived in a very humid environment like the Gulf Coast, they might realize that this is a ridiculous limitation. 
