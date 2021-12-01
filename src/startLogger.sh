#!/bin/bash

# Check if a python app is runnning
# serialLogger.py

# We define this as a command as we will use it more than once
# Could make this a function?
cmd="/bin/ps -ax | /bin/grep \"[s]erialLogger.py\""
eval "$cmd"

if [ $? == 0 ]; then
  echo "serialLogger.py is already running"
else
  echo "Starting serialLogger.py"
  /usr/bin/python3 /home/pi/repositories/logger/serialLogger.py  > /dev/null 2>&1 &
  eval "$cmd"
fi
