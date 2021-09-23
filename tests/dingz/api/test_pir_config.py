import json

from dingz.api import PIRConfig

SAMPLE_RESPONSE = json.loads(
    """
{
  "pir_output": 132,
  "pir_feedback": null,
  "feedback_intensity": 100,
  "thresholds": {
    "twilight_to_night": 20,
    "night_to_twilight": 26,
    "day_to_twilight": 44,
    "twilight_to_day": 50
  },
  "on_time": 10,
  "off_time": 300,
  "dim_value_night": 15,
  "dim_value_twilight": 15,
  "fade_in_time": 0,
  "fade_out_time": 0,
  "feedback_time": 1,
  "dimmer": [
    {
      "value_night": 15,
      "value_twilight": 15,
      "value_day": 0,
      "fade_in_time": 0,
      "fade_out_time": 0
    },
    {
      "value_night": 15,
      "value_twilight": 15,
      "value_day": 0,
      "fade_in_time": 0,
      "fade_out_time": 0
    },
    {
      "value_night": 15,
      "value_twilight": 15,
      "value_day": 0,
      "fade_in_time": 0,
      "fade_out_time": 0
    },
    {
      "value_night": 15,
      "value_twilight": 15,
      "value_day": 0,
      "fade_in_time": 0,
      "fade_out_time": 0
    }
  ],
  "enabled": true,
  "backoff_time": 10,
  "light_lpf": true
}
"""
)


def test_parse():
    data = PIRConfig.from_json(SAMPLE_RESPONSE)
    assert data
