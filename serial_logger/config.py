"""
Configuration values for the serial port logger
"""

PORT = "/dev/cu.usbmodem411"
BAUD = 115200
LOG_COUNT = 5
LOG_MAX_BYTES = 10000000
LOG_FILENAME = 'log.txt'
LOG_DURATION = 60 * 24  # used by event logger only

# If this file exists then we run
RUN_FLAG = 'delete-me-to-stop-logger'

# Command response logger config
MSG_BATTERY = ["adb", "shell", "dumpsys", "battery"]
MSG_TELEPHONY = ["adb", "shell", "dumpsys", "telephony.registry"]
LOG_PATH = '/tmp/neo_log.log'
