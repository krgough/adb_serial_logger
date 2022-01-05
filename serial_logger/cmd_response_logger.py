#!/usr/bin/env python3
""" Execute a command and log the response

"""
import subprocess
import logging.config
import serial_logger.config as cfg

LOGGER = logging.getLogger(__name__)


def configure_logger(name, log_path=None, console=True):
    """ Logger configuration function
        If logPath given then log to console and to the file
        else to console only.
    """
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "format": "%(asctime)s,%(levelname)s,%(name)s,%(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    }

    console_handler = {
        "level": "DEBUG",
        "class": "logging.StreamHandler",
        "formatter": "default",
        "stream": "ext://sys.stdout",
    }

    file_handler = {
        "level": "DEBUG",
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "filename": log_path,
        "maxBytes": 1024,
        "backupCount": 3,
    }

    active_handlers = []
    handlers = {}

    if log_path:
        active_handlers.append("file")
        handlers["file"] = file_handler

    if console or not log_path:
        active_handlers.append("console")
        handlers["console"] = console_handler

    logging.config.dictConfig({
        'version': version,
        'disable_existing_loggers': disable_existing_loggers,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': {'': {'level': 'DEBUG', 'handlers': active_handlers}},
    })

    return logging.getLogger(name)


def parse_adb_battery(data):
    """Parse the command response and return a dict

    Current Battery Service state:
      AC powered: false
      USB powered: true
      Wireless powered: false
      Max charging current: 0
      Max charging voltage: 0
      Charge counter: 301078
      status: 2
      health: 2
      present: true
      level: 66
      scale: 100
      voltage: 4110
      temperature: 360
      technology: Li-ion

    """
    new_data = []
    for row in data.splitlines()[1:]:
        row = row.split(':')
        new_data.append(f"{row[0].strip()}:{row[1].strip()}")

    return ",".join(new_data)


def execute_command(cmd):
    """Execute a command and return the response"""
    try:
        resp = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
        resp = parse_adb_battery(resp.stdout.decode('utf-8'))
        LOGGER.info(resp)
    except subprocess.CalledProcessError as err:
        resp = f"adb command failed. {err}"
        LOGGER.error(resp)
    return resp


def main(cmd):
    """Send a command and log the response"""
    try:
        resp = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
        resp = parse_adb_battery(resp.stdout.decode('utf-8'))
        LOGGER.info(resp)
    except subprocess.CalledProcessError as err:
        resp = f"adb command failed. {err}"
        LOGGER.error(resp)


if __name__ == "__main__":
    LOGGER = configure_logger(name=__name__, log_path="/tmp/junk.log")
    CMD = cfg.MSG
    execute_command(CMD)
