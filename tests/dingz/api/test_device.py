import json

from dingz.api import Device

SAMPLE_RESPONSE = json.loads(
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
)


def test_parse():
    device_raw = next(iter(SAMPLE_RESPONSE.values()))
    data = Device.from_json(device_raw)
    assert data
