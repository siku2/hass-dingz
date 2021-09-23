import json

from dingz.api import Info

SAMPLE_RESPONSE = json.loads(
    """
{
    "version": "1.3.25",
    "mac": "ABCDEFA81XYZ",
    "type": 108,
    "ssid": "...",
    "ip": "10.0.3.39",
    "mask": "255.255.240.0",
    "gw": "10.0.0.1",
    "dns": "10.0.0.1",
    "static": false,
    "connected": true
}
"""
)


def test_parse():
    data = Info.from_json(SAMPLE_RESPONSE)
    assert data
