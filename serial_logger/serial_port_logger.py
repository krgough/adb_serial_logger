#!/usr/bin/env python3
'''
@author: Keith Gough

Serial Port Logger - for logging serial port activity on a device

Implemented with threads and Queues - This was originally to support
sending commands on the serial port after some certain messages have
been received on the same serial port e.g. device sends a particular
debug message and then we send a command to the device to trigger
some wanted behaviour.

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

import serial_logger.config as cfg

STOP_THREAD = threading.Event()
THREAD_POOL = []

RX_QUEUE = queue.Queue(maxsize=1000)
TX_QUEUE = queue.Queue(maxsize=1000)

DEBUG = True
DATE_FORMAT = "%d/%m/%y %H:%M:%S.%f"

# Create a logger for general use
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
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
    cfg.LOG_FILENAME,
    maxBytes=cfg.LOG_MAX_BYTES,
    mode='a',
    backupCount=cfg.LOG_COUNT)
FILE_FMT = logging.Formatter('%(asctime)s,%(message)s', "%Y-%m-%d %H:%M:%S")
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
    ser = open_serial_port(cfg.PORT, cfg.BAUD)
    if not ser:
        sys.exit(1)
    start_serial_threads(ser)

    while os.path.exists(cfg.RUN_FLAG):
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
