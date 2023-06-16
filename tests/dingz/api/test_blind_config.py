import json

from dingz.api import BlindConfig

SAMPLE_RESPONSES = [
    json.loads(
        # API v2 response
        """
{
  "blinds": [
    {
      "active": true,
      "name": "Store Porte",
      "type": "blind",
      "min_value": 0,
      "max_value": 100,
      "def_blind": 0,
      "def_lamella": 80,
      "groups": "z",
      "auto_calibration": true,
      "shade_up_time": 55.65,
      "shade_down_time": 55.21,
      "invert_direction": false,
      "lamella_time": 1.4,
      "step_duration": 300,
      "step_interval": 1200,
      "state": "Initialised"
    },
    {
      "active": true,
      "name": "Store Fenêtre",
      "type": "blind",
      "min_value": 0,
      "max_value": 100,
      "def_blind": 0,
      "def_lamella": 80,
      "groups": "z",
      "auto_calibration": true,
      "shade_up_time": 47.55,
      "shade_down_time": 47.02,
      "invert_direction": false,
      "lamella_time": 1.4,
      "step_duration": 300,
      "step_interval": 1200,
      "state": "Initialised"
    }
  ]
}
"""
    ),
]


def test_parse():
    for response in SAMPLE_RESPONSES:
        data = BlindConfig.list_from_json(response["blinds"])
        assert len(data) == 2
