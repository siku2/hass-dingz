import json

from dingz.api import DimmerConfig

SAMPLE_RESPONSE = json.loads(
    """
{
  "dimmers": [
    {
      "output": "not_connected",
      "name": "",
      "feedback": null,
      "feedback_intensity": 100
    },
    {
      "output": "not_connected",
      "name": "",
      "feedback": null,
      "feedback_intensity": 1
    },
    {
      "output": "linear",
      "name": "Literally the sun",
      "feedback": null,
      "feedback_intensity": 1
    },
    {
      "output": "not_connected",
      "name": "",
      "feedback": null,
      "feedback_intensity": 1
    }
  ]
}
"""
)


def test_parse():
    data = DimmerConfig.list_from_json(SAMPLE_RESPONSE["dimmers"])
    assert len(data) == 4
