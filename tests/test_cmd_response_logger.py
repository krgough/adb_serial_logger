#!/usr/bin/env python3
"""
Tests for test_cmd_response_logger.py
"""

import pytest

from serial_logger import __version__
from serial_logger import cmd_response_logger as crl


def test_version():
    """Check the module version is correct"""
    assert __version__ == '0.1.0'


def test_failed_response():
    """Check error handling for failed command"""
    assert crl.execute_command(['false']) is None


def test_parse_battery():
    """Check the parsed battery response format"""

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


telephony_data = [
    (
        "  2022-01-06T09:29:12.892 - notifyServiceStateForSubscriber: subId=1 phoneId=0 state={mVoiceRegState=0(IN_SERVICE), mDataRegState=0(IN_SERVICE), mVoiceRoamingType=International Roaming, mDataRoamingType=International Roaming, mVoiceOperatorAlphaLong=vodafone UK, mVoiceOperatorAlphaShort=voda UK, mDataOperatorAlphaLong=vodafone UK, mDataOperatorAlphaShort=voda UK, isManualNetworkSelection=false(automatic), mRilVoiceRadioTechnology=14(LTE), mRilDataRadioTechnology=14(LTE), mCssIndicator=unsupported, mNetworkId=-1, mSystemId=-1, mCdmaRoamingIndicator=-1, mCdmaDefaultRoamingIndicator=-1, mIsEmergencyOnly=false, mIsDataRoamingFromRegistration=true, mIsUsingCarrierAggregation=false, mLteEarfcnRsrpBoost=0}",
        "Data_Radio=14(LTE)",
    ),
    (
        "Blah Blah Blah",
        "Data_Radio=Not found in telephony response",
    )
]


@pytest.mark.parametrize("test_input, expected", telephony_data)
def test_parse_telephony(test_input, expected):
    """Check the parsed battery response format"""
    assert crl.parse_adb_telephony(test_input) == expected
