'''
Created on 14 May 2017

@author: Keith Gough

Serial Port Logger - for logging serial port activity on a device

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

CRONTAB EDITS
-------------
Add these lines to crontab using 'crontab -e'
# Runs the bash script every 5mins that checks if logger is running
*/5 * * * * /home/pi/repositories/serialLogger/startLogging.sh > /dev/null 2>&1

'''


import sys
import datetime
import logging
import threading
import queue
import time
import os.path
from logging import handlers

import serial

STOP_THREAD = threading.Event()
THREAD_POOL = []

RX_QUEUE = queue.Queue(maxsize=1000)
TX_QUEUE = queue.Queue(maxsize=1000)

DEBUG = True
DATE_FORMAT = "%d/%m/%y %H:%M:%S.%f"

PORT = "//dev/cu.usbmodem411"
BAUD = 115200
LOG_COUNT = 5
LOG_MAX_BYTES = 10000000
LOG_FILENAME = 'log.txt'
RUN_FLAG = 'delete-me-to-stop-logger'  # If this file exists then we run

# Create a logger for general use
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER_HANDLER = logging.StreamHandler()  # This logs to stderr
LOGGER_FMT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    "%Y-%m-%d %H:%M:%S")
LOGGER_HANDLER.setFormatter(LOGGER_FMT)
LOGGER.addHandler(LOGGER_HANDLER)
# logging.basicConfig(level=logging.DEBUG)

# Create a logger for saving data
LOGGER_FILE = logging.getLogger()
LOGGER_FILE.setLevel(logging.INFO)

# Create and add a handler to the logger
HANDLER = handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=1000000, mode='a', backupCount=LOG_COUNT)
FILE_FMT = logging.Formatter('%(asctime)s:%(message)s', "%Y-%m-%d %H:%M:%S")
HANDLER.setFormatter(FILE_FMT)
LOGGER_FILE.addHandler(HANDLER)


def time_string():
    """ Returns a formatted time string
    """
    return datetime.datetime.now().strftime(DATE_FORMAT)


# Serial Thread Methods
def open_serial_port(port, baud):
    """ Open the given serial port
    """
    try:
        ser = serial.Serial(port, baud, timeout=1)
        LOGGER.info("Serial port opened...%s", port)
    except IOError as err:
        LOGGER.error('Error opening port: %s', err)
        return None
    return ser


def start_serial_threads(ser):
    """ Starts the wanted serial threads

        Stop any currently running read/write threads.
        Start the wanted ones.
        Interact with read/write is done via message queues rxQueue and txQueue
    """
    # Turn off any current threads
    stop_threads()

    # Start the wanted threads
    STOP_THREAD.clear()

    # Start the serial port read handler thread
    read_thread = threading.Thread(target=serial_read_handler, args=(ser,))
    read_thread.daemon = True  # This kills the thread when main program exits
    read_thread.start()
    read_thread.name = 'read_thread'
    THREAD_POOL.append(read_thread)


def stop_threads():
    """ Set the stop event and wait for all threads to exit
    """
    STOP_THREAD.set()
    for thd in THREAD_POOL:
        thd.join()


def serial_read_handler(ser):
    """ Serial port read thread handler
    """
    LOGGER.info('Serial readThread start')
    while not STOP_THREAD.is_set():
        try:
            reading = ser.readline().strip().decode()
        except UnicodeDecodeError:
            reading = ''

        if reading != '':
            # Make sure Qs are not full and blocking
            if RX_QUEUE.full():
                LOGGER.error("RxQueue is full.  Dumping oldest reading")
                RX_QUEUE.get()  # Dump last message from the rxQueue

            RX_QUEUE.put(reading)
            LOGGER.debug(reading)

    LOGGER.info('Serial readThread exit')


def start_serial_logger():
    """  Start the logger
    """
    # Open the serial port
    ser = open_serial_port(PORT, BAUD)
    if not ser:
        sys.exit(1)
    start_serial_threads(ser)

    while os.path.exists(RUN_FLAG):
        while not RX_QUEUE.empty():
            # Process the rxQueue
            data = RX_QUEUE.get()
            LOGGER_FILE.info(data)

        # No date in the rxQueue so sleep for a bit
        time.sleep(0.1)  # Sleep to let other processes run

    # Shutdown
    LOGGER.info('Run flag is missing.  Shutting down.')
    stop_threads()
    ser.close()
    logging.shutdown()


if __name__ == '__main__':
    start_serial_logger()
    print('All done.')
