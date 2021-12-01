'''
Created on 14 May 2017

@author: keith.gough

Log from he serial port and capture certain trigger events
Send commands on serial port if those events occur
Send a notification via email if the event occurs

'''
import logging.handlers
import datetime
import time
import os
import queue
import threading
import sys
from collections import namedtuple

import serial

import config as cfg

# Email notification parameters
EMAIL_TO = ['you.email@here.com']

SerialConfig = namedtuple('Serial_CFG', ['port', 'baud'])
SERIAL_CFG = SerialConfig(port=cfg.PORT, baud=cfg.BAUD)

LoggerConfig = namedtuple(
    'Logger_CFG', ['log_file', 'log_duration', 'log_count'])
LOGGER_CFG = LoggerConfig(
    log_file=cfg.LOG_FILENAME,
    log_duration=cfg.LOG_DURATION,
    log_count=cfg.LOG_COUNT
)

DEBUG = False
DATE_FORMAT = "%d/%m/%y %H:%M:%S.%f"

TRIGGER_STRING = 'junk_string'
DEBUG_CMDS = ['cmd1', 'cmd2']


# Helper methods
def time_string():
    """ Returns a formatted time string
    """
    return datetime.datetime.now().strftime(DATE_FORMAT)


def send_notification(email_to, subject, body, attachment_path):
    """ Send an email to notify user of some event
    """
    print("WARNING: sendNotification() function is not implemented.")
    print(f"{email_to},{subject}")
    print(f"{body}\n{attachment_path}")
    # kgmail.emailObject()


class PortLogger():
    # pylint: disable=too-many-instance-attributes
    """ Class to handle logging from the serial port
    """
    def __init__(self, name, logger_cfg, serial_cfg):
        self.name = name
        # self.runLogger = runLogger
        self.logger_cfg = logger_cfg
        self.serial_cfg = serial_cfg
        self.inter_char_delay = 0.02

        self.rx_queue = queue.Queue(maxsize=1000)
        self.tx_queue = queue.Queue(maxsize=1000)
        self.stop_threads_flag = threading.Event()
        self.thread_pool = []

        self.error = None

        # Start serial port.  Sets self.error on error
        self.ser = self.open_serial_port()

        # logger object
        self.logger = self.create_logger()
        self.logger.info("Serial logger started")

        # Start the serial port threads.
        # Adds thread references into self.threadPool
        if self.ser:
            self.start_serial_threads()

    def debug_print(self, message):
        """ Print a debug string
        """
        if DEBUG:
            print(f"{time_string()},{self.name},{message}")

    def create_logger(self):
        """ Create the logger
        """
        logger = logging.getLogger(self.name + '_logger')
        logger.setLevel(logging.INFO)

        # Create and add a handler to the logger
        handler = logging.handlers.TimedRotatingFileHandler(
            self.logger_cfg.log_file,
            when='m',
            interval=self.logger_cfg.log_duration,
            backupCount=self.logger_cfg.log_count)
        logger.addHandler(handler)

        # Create and add a message formatter to the handler
        formatter = logging.Formatter(f"%(asctime)s,{self.name},%(message)s")
        handler.setFormatter(formatter)

        return logger

    def open_serial_port(self):
        """ Open the given serial port
        """
        try:
            ser = serial.Serial(
                self.serial_cfg.port,
                self.serial_cfg.baud,
                timeout=1)
            self.debug_print(
                f"Serial port opened...{self.serial_cfg.port}")
        except IOError as err:
            error_string = f'Error opening port. {err}'
            self.error = error_string
            self.debug_print(error_string)
            return None
        return ser

    def start_serial_threads(self):
        """ Starts the read/write serial threads

            Stop any currently running threads and start the wanted ones.
            Interact with read/write is done via message queues rxQueue
            and txQueue
        """
        # Turn off any current threads
        self.stop_threads()

        # Start the wanted threads
        self.thread_pool = []
        self.stop_threads_flag.clear()

        # Start the serial port read handler thread
        read_thread = threading.Thread(target=self.serial_read_handler)
        read_thread.daemon = True  # kills thread when main program exits
        read_thread.start()
        read_thread.name = 'readThread'
        self.thread_pool.append(read_thread)

        # Start the serial write handler thread
        write_thread = threading.Thread(target=self.serial_write_handler)
        write_thread.daemon = True  # kills thread when main program exits
        write_thread.start()
        write_thread.name = 'writeThread'
        self.thread_pool.append(write_thread)

        # Start the rxQueue handler thread
        write_thread = threading.Thread(target=self.rx_queue_handler)
        write_thread.daemon = True  # Kills thread when main program exits
        write_thread.start()
        write_thread.name = 'rxQueueHandlerThread'
        self.thread_pool.append(write_thread)

    def stop_threads(self):
        """ Set the stop event and wait for all threads to exit
        """
        self.stop_threads_flag.set()
        for thd in self.thread_pool:
            thd.join()

    def serial_read_handler(self):
        """ Serial port read thread handler
        """
        self.debug_print('Serial readThread start')
        while not self.stop_threads_flag.is_set():
            reading = self.ser.readline().decode().strip()
            if reading != '':
                # Make sure Qs are not full and blocking
                if self.rx_queue.full():
                    msg = (f"""{time_string()},Rx,*** DEBUG: """
                           """rxQueue is full. Dumping oldest message""")
                    self.debug_print(msg)
                    self.logger.info(msg)
                    self.rx_queue.get()  # Dump last message from the rxQueue

                self.rx_queue.put(reading)

                # Log the string and debug print if debug enabled
                msg = f"Rx,{reading}"
                self.logger.info(msg)
                self.debug_print(msg)
        self.debug_print('Serial readThread exit')

    def serial_write_handler(self):
        """ Serial port write handler

            Get from a queue.
            Blocks if queue is empty so we just loop
            and wait for items
        """
        self.debug_print('Serial writeThread start')
        while not self.stop_threads_flag.is_set():

            msg = self.tx_queue.get()  # Blocks until item available
            self.debug_print(f"Tx,{msg}")

            msg = '\r' + msg + '\r'
            for char in msg:
                time.sleep(self.inter_char_delay)
                self.ser.write(bytearray(char, 'ascii'))

            self.logger.info("Tx,%s", msg)
        self.debug_print('Serial writeThread exit')

    def rx_queue_handler(self):
        """ This thread checks the rx_queue for trigger strings and if found it sends
            some debug commands to the device to trigger additional data to be
            sent to the logfiles.
        """
        self.debug_print('rxQueue handler thread start')
        while not self.stop_threads_flag.is_set():

            # Process the rx_queue
            msg = self.rx_queue.get()  # Blocks until item available

            # If we see a TRIGGER_STRING i.e. suspected corruption then
            # send the debug commands
            if TRIGGER_STRING in msg:
                time.sleep(5)  # Sleep to let dump complete

                for char in DEBUG_CMDS:
                    self.tx_queue.put(char)
                    time.sleep(2)

                send_notification(
                    EMAIL_TO,
                    "Sensor corruption.  Download the logs.",
                    "Sensor corruption.  Download the logs.",
                    self.logger_cfg.log_file)

                self.logger.info("EVENT CAPTURED. EMAIL SENT.")

        self.debug_print('rxQueue handler thread stop')


def main():
    """ Main program
    """
    # Create a run flag file, makes it easy to stop script by deleting the file
    open(cfg.RUN_FLAG, "w", encoding='utf-8').close()

    # Instantiate the number of wanted portLoggers
    wds_port = PortLogger(name='wdsPort',
                          logger_cfg=LOGGER_CFG,
                          serial_cfg=SERIAL_CFG)

    port_logger_list = [wds_port]

    # Exit with debug if errors found
    for p_logger in port_logger_list:
        if p_logger.error:
            print(f"ERROR: {p_logger.name},{p_logger.error}")
            sys.exit()

    # Loop until run_flag is deleted (typically run forever)
    while os.path.exists(cfg.RUN_FLAG):
        time.sleep(1)

    # Shutdown the threads nicely
    for p_logger in port_logger_list:
        p_logger.stop_threads()

    print('All Done')


if __name__ == '__main__':
    main()
