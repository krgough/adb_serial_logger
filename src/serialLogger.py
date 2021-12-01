'''
Created on 14 May 2017

@author: keith.gough

Serial Port Logger Class

Includes functionality to look for a wanted string in the incomming queue.
If the target string is found then some commands can be sent to the device
to trigger data exchange and an alert email can be sent.

'''
import logging.handlers
import datetime
import time
import os
import queue
import threading

import serial

""" Email notification parameters """
EMAIL_TO = ['keith.gough@hivehome.com']

RUN_FLAG = 'serial-logger-delete-me-to-stop-running'

LOGFILE_PATH = './'
LOG_DURATION = 60*24
LOG_COUNT = 7

SERIAL_PORT = '/dev/cu.usbmodem411'
BAUD = 115200

DEBUG = False
DATE_FORMAT = "%d/%m/%y %H:%M:%S.%f"


# Helper methods
def myTimeStr():
    """ Returns a formatted time string
    """
    return datetime.datetime.now().strftime(DATE_FORMAT)


def sendNotification(emailTo, subject, body, attachmentPath):
    """ Send an email to notify user of some event
    """
    print("WARNING: sendNotification() function is not implemented.")
    print("{},{}".format(emailTo, subject))
    print("{}\n{}".format(body, attachmentPath))
    # kgmail.emailObject()
    return


class PortLogger():
    # pylint: disable=too-many-instance-attributes
    """ Class to handle logging from the serial port
    """
    #def __init__(self, name, runLogger, logFile, logDuration, logCount, port, baud):
    def __init__(self, name, logFile, logDuration, logCount, port, baud):
        self.name = name
        #self.runLogger = runLogger
        self.logFile = logFile
        self.logDuration = logDuration
        self.logCount = logCount
        self.port = port
        self.baud = baud
        self.interCharDelay = 0.02

        self.rxQueue = queue.Queue(maxsize=1000)
        self.txQueue = queue.Queue(maxsize=1000)
        self.stopThreadsFlag = threading.Event()
        self.threadPool = []

        self.error = None

        # Start serial port.  Sets self.error on error
        self.ser = self.openSerialPort()

        # logger object
        self.logger = self.createLogger()
        self.logger.info("Serial logger started")

        #  Start the serial port threads. Adds thread references into self.threadPool
        if self.ser: self.startSerialThreads()

        return

    def debug_print(self, message):
        """ Print a debug string
        """
        if DEBUG: print("{},{},{}".format(myTimeStr(), self.name, message))
        return

    def create_logger(self):
        """ Create the logger
        """
        logger = logging.getLogger(self.name + '_logger')
        logger.setLevel(logging.INFO)

        # Create and add a handler to the logger
        handler = logging.handlers.TimedRotatingFileHandler(
            self.logFile,
            when='m',
            interval=self.logDuration,
            backupCount=self.logCount)
        logger.addHandler(handler)

        # Create and add a message formatter to the handler
        formatter = logging.Formatter("%(asctime)s,{},%(message)s".format(self.name))
        handler.setFormatter(formatter)

        return logger

    def open_serial_port(self):
        """ Open the given serial port
        """
        try:
            ser = serial.Serial(self.port, self.baud, timeout=1)
            self.debug_print("Serial port opened...{0}".format(self.port))
        except IOError as e:
            error_string = 'Error opening port. {}'.format(e)
            self.error = error_string
            self.debug_print(error_string)
            return None
        return ser

    def start_serial_threads(self):
        """ Starts the read/write serial threads

            Stop any currently running threads and start the wanted ones.
            Interact with read/write is done via message queues rxQueue and txQueue

        """
        # Turn off any current threads
        self.stopThreads()

        # Start the wanted threads
        self.threadPool = []
        self.stopThreadsFlag.clear()

        # Start the serial port read handler thread
        readThread = threading.Thread(target=self.serialReadHandler)
        readThread.daemon = True # This kills the thread when main program exits
        readThread.start()
        readThread.name = 'readThread'
        self.threadPool.append(readThread)

        # Start the serial write handler thread
        writeThread = threading.Thread(target=self.serialWriteHandler)
        writeThread.daemon = True # This kills the thread when main program exits
        writeThread.start()
        writeThread.name = 'writeThread'
        self.threadPool.append(writeThread)

        # Start the rxQueue handler thread
        writeThread = threading.Thread(target=self.rxQueueHandler)
        writeThread.daemon = True # This kills the thread when main program exits
        writeThread.start()
        writeThread.name = 'rxQueueHandlerThread'
        self.threadPool.append(writeThread)

        return
    def stopThreads(self):
        """ Set the stop event and wait for all threads to exit

        """
        self.stopThreadsFlag.set()
        for t in self.threadPool:
            t.join()
        return
    def serialReadHandler(self):
        """ Serial port read thread handler

        """
        self.debugPrint('Serial readThread start')
        while not self.stopThreadsFlag.isSet():
            reading = self.ser.readline().decode().strip()
            if reading != '':
                myTime = myTimeStr()
                # Make sure Qs are not full and blocking
                if self.rxQueue.full():
                    myString = "{},Rx,*** DEBUG: rxQueue is full.  Dumping oldest message'".format(myTime)
                    self.debugPrint(myString)
                    self.logger.info(myString)
                    self.rxQueue.get() # Dump last message from the rxQueue

                self.rxQueue.put(reading)

                # Log the string and debug print if debug enabled
                myString = "Rx,{}".format(reading)
                self.logger.info(myString)
                self.debugPrint("Rx,{}".format(myString))
        self.debugPrint('Serial readThread exit')
        return
    def serialWriteHandler(self):
        """ Serial port write handler

            Get from a queue blocks if queue is empty so we just loop
            and wait for items

        """
        self.debugPrint('Serial writeThread start')
        while not self.stopThreadsFlag.isSet():

            myMessage = self.txQueue.get() # Blocks until item available on the q
            self.debugPrint("Tx,{}".format(myMessage))

            myMessage = '\r' + myMessage + '\r'
            for ch in myMessage:
                time.sleep(self.interCharDelay)
                self.ser.write(bytearray(ch, 'ascii'))

            self.logger.info("Tx,%s", myMessage)
        self.debugPrint('Serial writeThread exit')
        return

    def rxQueueHandler(self):
        """ This thread checks the rxQueue for trigger strings and if found it sends
            some debug commands to the device to trigger additional data to be sent to
            the logfiles.

        """
        self.debugPrint('rxQueue handler thread start')
        while not self.stopThreadsFlag.isSet():

            ''' Process the rxQueue '''
            myString = self.rxQueue.get()  # Blocks until item available

            # If we see a TRIGGER_STRING i.e. suspected corruption then send the debug commands
            if TRIGGER_STRING in myString:
                time.sleep(5) # Sleep to let dump complete

                for ch in DEBUG_CMDS:
                    self.txQueue.put(ch)
                    time.sleep(2)

                sendNotification(EMAIL_TO, "Sensor corruption.  Download the logs.", "Sensor corruption.  Download the logs.", self.logFile)
                self.logger.info("EVENT CAPTURED. EMAIL SENT.")

        self.debugPrint('rxQueue handler thread stop')
        return


def main():
    """ Main program
    """
    # Create a run flag file, makes it easy to stop script by deleting the file
    open(RUN_FLAG, "w").close()

    # Instantiate the number of wanted portLoggers
    wdsPort = portLogger(name='wdsPort',
                         logFile=LOGFILE_PATH + 'wdsLog',
                         logDuration=LOG_DURATION, # Number of minutes per logfile
                         logCount=LOG_COUNT,    # Number of rotated logfiles
                         port=SERIAL_PORT,
                         baud=BAUD)

    portLoggerList = [wdsPort]

    # Exit with debug if errors found
    for pl in portLoggerList:
        if pl.error:
            print("ERROR: {},{}".format(pl.name, pl.error))
            exit()

    # Loop until run_flag is deleted (typically run forever)
    while os.path.exists(RUN_FLAG):
        time.sleep(1)

    # Shutdown the threads nicely
    for pl in portLoggerList:
        pl.stopThreads()

    print('All Done')

if __name__ == '__main__':
    main()
