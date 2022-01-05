# Serial Port Logger - Logging serial port activity from a device

## Logging output from a command line command:
---
Send a command and log the response e.g.

```
adb shell dumpsys battery

Current Battery Service state:  
  AC powered: false
  USB powered: true
  Wireless powered: false
  Max charging current: 0
  Max charging voltage: 0
  Charge counter: 207050
  status: 2
  health: 2
  present: true
  level: 43
  scale: 100
  voltage: 3983
  temperature: 360
  technology: Li-ion
```


## Logging from serial port:
-----------

Debug data being sent to the serial port is captured and logged in rotating
log files. Connect the serial port on the DUT to the logging device serial
port and edit the setup below to setup baudrates and logging policy.

Edit the crontab file to start this logging script if process stops or logging
device is reset for some reason.

Dependencies:
-------------
Install with...
```
pip3 install -r requirements.txt
```

CRONTAB EDITS
-------------
Add these lines to crontab using 'crontab -e'
```
# Runs the bash script every 5mins that checks if logger is running
*/5 * * * * /home/<Path-to-repo>/serial_logger/serial_logger/startLogger.sh > /dev/null 2>&1 & 
```
