import json

from dingz.api import SystemConfig

SAMPLE_RESPONSE = json.loads(
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
)


def test_parse():
    data = SystemConfig.from_json(SAMPLE_RESPONSE)
    assert data
