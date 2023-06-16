import json

from dingz.api import Device

SAMPLE_RESPONSES = [
    json.loads(
        """
{
  "ABCDEFA81XYZ": {
    "type": "dingz",
    "battery": false,
    "reachable": true,
    "meshroot": true,
    "fw_version": "1.3.25",
    "hw_version": "1.1.2",
    "fw_version_puck": "1.1.28",
    "bl_version_puck": "1.0.0",
    "hw_version_puck": "1.1.2",
    "hw_id_puck": 65535,
    "puck_sn": "B20010000010",
    "puck_production_date": {
      "year": 20,
      "month": 4,
      "day": 29
    },
    "dip_config": 3,
    "puck_hw_model": "DZ1B-4CH",
    "front_hw_model": "dz1f-pir",
    "front_production_date": "20/4/29",
    "front_sn": "F20042900000",
    "has_pir": true,
    "hash": "db4f36f7"
  }
}
"""
    ),
    json.loads(
        # API v2 has apparently:
        # + dip_misconf
        # + dip_static
        # + front_color
        """
  {
  "ABCDEFA81XYZ": {
    "type": "dingz",
    "battery": false,
    "reachable": true,
    "meshroot": true,
    "fw_version": "2.0.21",
    "hw_version": "1.1.2",
    "fw_version_puck": "2.1.4",
    "bl_version_puck": "1.0.0",
    "hw_version_puck": "1.1.2",
    "hw_id_puck": 65535,
    "puck_sn": "B20092900007",
    "puck_production_date": {
      "year": 20,
      "month": 9,
      "day": 29
    },
    "dip_config": 0,
    "dip_static": false,
    "dip_misconf": false,
    "puck_hw_model": "DZ1B-4CH",
    "front_hw_model": "dz1f-4b",
    "front_production_date": "21/3/18",
    "front_sn": "F21031800317",
    "front_color": "WH",
    "has_pir": false,
    "hash": "a853cc0d"
  }
}
"""
    ),
]


def test_parse():
    for response in SAMPLE_RESPONSES:
        device_raw = next(iter(response.values()))
        data = Device.from_json(device_raw)
        assert data
