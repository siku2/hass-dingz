import json

from dingz.api import State

SAMPLE_RESPONSE = json.loads(
    """
{
  "dimmers": [
    {
      "on": false,
      "output": 0,
      "ramp": 0,
      "readonly": true,
      "index": {
        "relative": 0,
        "absolute": 0
      }
    },
    {
      "on": false,
      "output": 0,
      "ramp": 0,
      "readonly": true,
      "index": {
        "relative": 1,
        "absolute": 1
      }
    },
    {
      "on": false,
      "output": 0,
      "ramp": 0,
      "readonly": false,
      "index": {
        "relative": 2,
        "absolute": 2
      }
    },
    {
      "on": false,
      "output": 0,
      "ramp": 0,
      "readonly": true,
      "index": {
        "relative": 3,
        "absolute": 3
      }
    }
  ],
  "blinds": [],
  "led": {
    "on": false,
    "hsv": "0;100;40",
    "rgb": "FFFFFF",
    "mode": "hsv",
    "ramp": 25
  },
  "sensors": {
    "brightness": 1,
    "light_state": "night",
    "room_temperature": 21.5,
    "uncompensated_temperature": 38.875,
    "temp_offset": 0.8,
    "cpu_temperature": 55.56,
    "puck_temperature": 40,
    "fet_temperature": 41.6,
    "input_state": false,
    "person_present": 0,
    "light_off_timer": 0,
    "suspend_timer": 0,
    "power_outputs": [
      {
        "value": 0
      },
      {
        "value": 0
      },
      {
        "value": 0
      },
      {
        "value": 0
      }
    ]
  },
  "thermostat": {
    "active": false,
    "out": 0,
    "on": false,
    "enabled": true,
    "target_temp": 21,
    "mode": "heating",
    "temp": 21.5,
    "min_target_temp": 17,
    "max_target_temp": 31
  },
  "wifi": {
    "version": "1.3.25",
    "mac": "ABCDEFA81XYZ",
    "ssid": "...",
    "ip": "10.0.3.39",
    "mask": "255.255.240.0",
    "gateway": "10.0.0.1",
    "dns": "10.0.0.1",
    "static": false,
    "connected": true
  },
  "time": "2021-09-23 22:07:09",
  "config": {
    "timestamp": 1628872687
  }
}
"""
)


def test_parse():
    data = State.from_json(SAMPLE_RESPONSE)
    assert data
