# Serial Port Logger - for logging serial port activity on a device

Operating Instructions:
-----------------------
Debug data being sent to the serial port is captured and logged in rotating
log files. Connect the serial port on the DUT to the logging device serial
port and edit the setup below to setup baudrates and logging policy.

Edit the crontab file to start this logging script if process stops or logging
device is reset for some reason.

Dependencies:
-------------
pyserial - install with 'pip3 install pyserial'
Add these lines to crontab using 'crontab -e'

CRONTAB EDITS
-------------
```
# Runs the bash script every 5mins that checks if logger is running
*/5 * * * * /home/<Path-to-repo>/serial_logger/serial_logger/startLogger.sh > /tmp/logger
```
