#!/bin/bash

# Check if a python app is runnning
# serial_logger.py

# We define this as a command as we will use it more than once
# Could make this a function?
cmd="/bin/ps -ax | /bin/grep \"[s]erial_logger.py\""
eval "$cmd"

if [ $? == 0 ]; then
  echo "serial_logger.py is already running"
else
  echo "Starting serial_logger.py"
  /usr/bin/python3 /home/keith/repositories/serial_logger/serial_logger/serial_logger.py &
  eval "$cmd"
fi
