#!/usr/bin/env python3
'''
21/06/2018 Keith Gough

Binary Port Logger - for logging serial port activity on a device.

This script assumes the device is generating serial binary logging data at a given Baud rate.
Connect the Rx pin of the logging device serial port to the device generating data.

Dependencies:
-------------
pyserial - install with 'pip3 install serial'

'''


import datetime
import threading
import queue
import time
import os
import getopt
import sys
import glob
import serial

STOP_THREAD = threading.Event()
THREAD_POOL = []

RX_QUEUE = queue.Queue(maxsize=1000)
TX_QUEUE = queue.Queue(maxsize=1000)

DEBUG = True
DATE_FORMAT = "%d/%m/%y %H:%M:%S.%f"

PORT = "/dev/tty.usbserial-FT1UL06Y"
BAUD = 3000000
LOG_MAX_COUNT = 5
LOG_MAX_BYTES = 1000
LOG_FILENAME = '/Users/Keith.Gough/wifi-binary-logs'

def getAttrs():
    """ Get CLI parameters
    """
    helpString  = '***\n'
    helpString += 'USAGE: {} -p port -b baud -c max_file_count -s max_bytes_per_file -f log_filename [-h]\n'.format(__file__)
    helpString += '-p <serial port name>\n'
    helpString += '-b <baud>                 3000000 for wifi fw debug port\n'
    helpString += '-c <max_file count>       For log rotations\n'
    helpString += '-s <max_bytes_per_file    For log rotations\n'
    helpString += '-f <log_filename>\n'
    helpString += '-h                        Show this help\n'

    try:
        options,_ = getopt.getopt(sys.argv[1:],"h-p:-b:-c:-s:-f:")

    except getopt.GetoptError:
        print('\n*** INVALID OPTIONS')
        print(helpString)
        exit()

    port = None
    baud = None
    logMaxCount = None
    logMaxBytes = None
    logFilename = None

    for opt,arg in options:
        if opt == '-h':
            print(helpString)
            exit()
        elif opt == '-p':
            port = arg
        elif opt == '-b':
            baud = arg
        elif opt == '-c':
            logMaxCount = int(arg)
        elif opt == '-s':
            logMaxBytes = int(arg)
        elif opt == '-f':
            logFilename = arg

    if port is None or baud is None or logMaxBytes is None or logMaxCount is None or logFilename is None:
        print("\n*** ERROR:  You missed a required parameter\n")
        print(helpString)
        exit()

    return port, baud, logMaxCount, logMaxBytes, logFilename

def myTimeStr():
    """ Returns a formatted time string

    """
    return datetime.datetime.now().strftime(DATE_FORMAT)

""" Serial Thread Methods """
def openSerialPort(port,baud):
    """ Open the given serial port

    """
    try:
        ser=serial.Serial(port, baud, timeout=1)
        print("Serial port opened...{0}".format(port))
    except IOError as e:
        print('Error opening port.',e)
        return None
    return ser
def startSerialThreads(ser):
    """ Starts the wanted serial threads

        Stop any currently running read/write threads and start the wanted ones.
        Interact with read/write is done via message queues rxQueue and txQueue

    """
    # Turn off any current threads
    stopThreads()

    # Start the wanted threads
    STOP_THREAD.clear()

    # Start the serial port read handler thread
    readThread = threading.Thread(target=serialReadHandler, args=(ser,))
    readThread.daemon = True # This kills the thread when main program exits
    readThread.start()
    readThread.name = 'readThread'
    THREAD_POOL.append(readThread)

    return
def stopThreads():
    """ Set the stop event and wait for all threads to exit

    """
    STOP_THREAD.set()
    for t in THREAD_POOL:
        t.join()
    return
def serialReadHandler(ser):
    """ Serial port read thread handler

    """
    print('Serial readThread start')
    while not STOP_THREAD.isSet():
        reading = ser.read()
        if reading != '':
            myTime = myTimeStr()
            # Make sure Qs are not full and blocking
            if RX_QUEUE.full():
                myString = "{},Rx,*** DEBUG: rxQueue is full.  Dumping oldest message'".format(myTime)
                if DEBUG: print(myString)
                RX_QUEUE.get() # Dump last message from the rxQueue

            RX_QUEUE.put(reading)
            if DEBUG: print("DEBUG:{}".format(reading))

    print('Serial readThread exit')
    return
def doLogFileRotate(filehandle):
    """ Search for all files matching the base filename
        For each file:

        if filname number larger than max count then delete it
        else: increment the file number.

        Rename the current base file (the current working log file) to rotated file number 1.

    """
    filelist = sorted(glob.glob(filehandle.name + "*"),reverse=True)
    filelist.remove(filehandle.name)  # Remove the wokring logfile from the list
    print(filelist)

    # Rotate the filenames for existing logs files to make space for new 'log.1' file.
    for f in filelist:
        fileNumber=int(f[len(filehandle.name)+1:])
        if fileNumber>=LOG_MAX_COUNT:
            os.remove(f)
        else:
            os.rename(f, "{}.{}".format(filehandle.name,fileNumber + 1))

    # Now rename working log to 'log.1' and open a new working logfile
    filehandle.close()
    os.rename(LOG_FILENAME,"{}.1".format(LOG_FILENAME))
    newHandle = open(LOG_FILENAME,'ab',buffering=0)

    return newHandle
def fileRotateRequired(filename):
    """ Return the size of the given file

    """
    fileSize = os.path.getsize(filename)
    return bool(fileSize > LOG_MAX_BYTES)
def binaryLogger():
    """ Write data from rxQ to the base logfile
        Check if base file has exceeded maxium size
        If base file has exceeded maximum size then:
            close the base log file
            do the log file rotations
            open a new base logfile
    """

    f = open(LOG_FILENAME,'ab',buffering=0)

    while True:
        if fileRotateRequired(LOG_FILENAME):
            f = doLogFileRotate(f)

        else:
            while not RX_QUEUE.empty():
                # Process the rxQueue
                data = RX_QUEUE.get()
                f.write(data)

            # No data in the rxQueue so sleep for a bit to let other processes run
            time.sleep(0.1)

    return

if __name__=='__main__':
    PORT,BAUD,LOG_MAX_COUNT,LOG_MAX_BYTES,LOG_FILENAME = getAttrs()
    SER = openSerialPort(PORT, BAUD)
    if SER is None: exit()
    startSerialThreads(SER)

    binaryLogger()

    print('All done.')
