import json

from dingz.api import State

SAMPLE_RESPONSES = [
    json.loads(
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
    ),
    # API v2 state; has
    # - sensors.person_present
    json.loads(
        """
{
  "dimmers": [],
  "blinds": [
    {
      "moving": "stop",
      "position": 100,
      "lamella": 100,
      "readonly": false,
      "index": {
        "relative": 0,
        "absolute": 0
      }
    },
    {
      "moving": "stop",
      "position": 100,
      "lamella": 100,
      "readonly": false,
      "index": {
        "relative": 1,
        "absolute": 1
      }
    }
  ],
  "led": {
    "on": false,
    "hsv": "91;100;0",
    "rgb": "FFFFFF",
    "mode": "hsv",
    "ramp": 25
  },
  "sensors": {
    "brightness": 681,
    "light_state": "day",
    "light_state_lpf": "day",
    "room_temperature": 25.5,
    "uncompensated_temperature": 37.375,
    "temp_offset": 6,
    "cpu_temperature": 45,
    "puck_temperature": 37,
    "fet_temperature": 38,
    "input_state": null,
    "pirs": [
      null,
      {
        "enabled": false,
        "motion": false,
        "mode": "idle",
        "light_off_timer": 0,
        "suspend_timer": 0
      }
    ],
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
  "dyn_light": {
    "mode": "day"
  },
  "thermostat": {
    "active": false,
    "state": "off",
    "mode": "off",
    "enabled": false,
    "target_temp": 21,
    "min_target_temp": 17,
    "max_target_temp": 31,
    "temp": 25.5
  },
  "wifi": {
    "version": "2.0.21",
    "mac": "F008D1C3A4F0",
    "ssid": "HermineOriole",
    "ip": "10.40.2.53",
    "mask": "255.255.255.0",
    "gateway": "10.40.2.1",
    "dns": "10.40.2.1",
    "static": false,
    "connected": true
  },
  "cloud": {
    "aws": "connected"
  },
  "time": "2023-06-16 17:19:46",
  "config": {
    "timestamp": 1686804173
  }
}
"""
    ),
]


def test_parse():
    for response in SAMPLE_RESPONSES:
        data = State.from_json(response)
        assert data
