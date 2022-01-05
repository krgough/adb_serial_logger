#!/usr/bin/env python3
"""
Tests for test_cmd_response_logger.py
"""

from serial_logger import __version__
from serial_logger import cmd_response_logger as crl


def test_version():
    """Check the module version is correct"""
    assert __version__ == '0.1.0'


def test_failed_response():
    """Check error handling for failed command"""
    assert crl.execute_command(['false']).startswith('adb command failed.')


def test_parse_response():
    """Check the parsed response format"""

    test_data = {
        'data': (
            """Current Battery Service state:\n"""
            """  AC powered: false\n"""
            """  USB powered: true\n"""
            """  Wireless powered: false\n"""
            """  Max charging current: 0\n"""
            """  Max charging voltage: 0\n"""
            """  Charge counter: 470066\n"""
            """  status: 5\n"""
            """  health: 2\n"""
            """  present: true\n"""
            """  level: 100\n"""
            """  scale: 100\n"""
            """  voltage: 4328\n"""
            """  temperature: 320\n"""
            """  technology: Li-ion\n"""
        ),
        "parsed_correct": (
            "AC powered:false,USB powered:true,Wireless powered:false,"
            "Max charging current:0,Max charging voltage:0,"
            "Charge counter:470066,status:5,health:2,present:true,"
            "level:100,scale:100,voltage:4328,temperature:320,technology:Li-ion"
        ),
    }
    print(test_data['data'])
    assert test_data["parsed_correct"] == crl.parse_adb_battery(test_data['data'])
