import json

from dingz.api import SystemConfig

SAMPLE_RESPONSES = [
    json.loads(
        """
{
  "allow_reset": true,
  "allow_wps": true,
  "allow_reboot": true,
  "broadcast_period": 5,
  "mdns_search_period": 60,
  "origin": true,
  "upgrade_blink": true,
  "reboot_blink": false,
  "dingz_name": "dingz",
  "room_name": "Hell",
  "temp_offset": 0.8,
  "fet_offset": 0,
  "cpu_offset": 25.2,
  "groups": [
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false
  ],
  "temp_comp": {
    "fet_offset": 2.640000104904175,
    "gain_up": 0.012000000104308128,
    "gain_down": 0.006000000052154064,
    "gain_total": 0.25
  },
  "time": "2021-09-23 22:10:02",
  "system_status": "OK"
}
"""
    ),
    json.loads(
        # API v2 has at least :
        # - broadcast_period less
        """
{
  "protected_status": false,
  "allow_reset": true,
  "allow_wps": true,
  "allow_reboot": true,
  "allow_remote_reboot": false,
  "origin": true,
  "upgrade_blink": true,
  "reboot_blink": false,
  "dingz_name": "dingz",
  "room_name": "Cuisine",
  "id": "f008d1c3a4f0",
  "temp_offset": 6,
  "fet_offset": 2.5,
  "cpu_offset": 26.4,
  "temp_comp": {
    "fet_offset": 2.64,
    "gain_up": 0.012,
    "gain_down": 0.006,
    "gain_total": 0.25
  },
  "sun_offset": 0,
  "tzid": 0,
  "lat": 10.0000,
  "long": 0.1234,
  "dyn_light": {
    "enable": true,
    "phases": 3,
    "source": "sun",
    "sun_offset": {
      "day": 30,
      "twilight": 30,
      "night": 30
    }
  },
  "wifi_ps": true,
  "time": "2023-06-16 17:15:10",
  "sunrise": {
    "hour": 5,
    "minute": 36
  },
  "sunset": {
    "hour": 21,
    "minute": 27
  },
  "system_status": "OK"
}
"""
    ),
]


def test_parse():
    for response in SAMPLE_RESPONSES:
        data = SystemConfig.from_json(response)
        assert data
