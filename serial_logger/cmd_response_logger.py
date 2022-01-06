#!/usr/bin/env python3
""" Execute a command and log the response

"""
import subprocess
import logging.config
import re
import serial_logger.config as cfg

LOGGER = logging.getLogger(__name__)


def configure_logger(name, log_path=None, console=True):
    """Logger configuration function
    If log_path given then log to console and to the file
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

    logging.config.dictConfig(
        {
            "version": version,
            "disable_existing_loggers": disable_existing_loggers,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": {"": {"level": "DEBUG", "handlers": active_handlers}},
        }
    )

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
        row = row.split(":")
        new_data.append(f"{row[0].strip()}:{row[1].strip()}")

    return ",".join(new_data)


def parse_adb_telephony(data):
    """Parse the telephony.registry response for mRilDataRadioTechnology
    We assume the value of that parameter is the network type e.g. LTE or GSM
    """
    # data = [d.strip().split(", ") for d in data.splitlines()]
    search_string = "mRilDataRadioTechnology=(.*?),"
    match = re.search(search_string, data)
    data_radio = match.group(1) if match else "Not found in telephony response"
    return f"Data_Radio={data_radio}"


def execute_command(cmd):
    """Execute a command and return the response"""
    try:
        resp = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        LOGGER.error("adb command failed. cmd=%s, err=%s", cmd, err)
        resp = None
    return resp


def main(commands):
    """Send a command and log the response"""

    for cmd in commands:
        resp = execute_command(cmd)
        if resp and cmd == cfg.MSG_BATTERY:
            resp = parse_adb_battery(resp.stdout.decode("utf-8"))

        if resp and cmd == cfg.MSG_TELEPHONY:
            resp = parse_adb_telephony(resp.stdout.decode('utf-8'))

        LOGGER.info(resp)


if __name__ == "__main__":
    # LOGGER = configure_logger(name=__name__, log_path="/tmp/junk.log")
    LOGGER = configure_logger(name=__name__, log_path=cfg.LOG_PATH)
    main([cfg.MSG_TELEPHONY, cfg.MSG_BATTERY])
