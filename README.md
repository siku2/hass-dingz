# Home Assistant dingz

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories)

A custom component for [dingz](https://www.dingz.ch/) wall switches.

After installing the component with [HACS](https://hacs.xyz) you'll find a new integration called "dingz".
Automatic discovery currently isn't supported and you're strongly encouraged to use a static IP or a hostname.

## Supported Features

- Panel LED
- Dimmers (for dimmers to be detected they must have a name)
- Brightness sensor
- PIR (Motion) sensor (must be present and enabled)
- Temperature sensors
- Input
- Blinds / Shades (position and tilt)

## Unsupported Features

- Thermostat

These are unsupported because I can't test them.
If you would like to see support for any of these, don't hesitate to open an issue.

### Planned Features

- Use a generic action to send events to Home Assistant. This will allow the reduction of the polling interval as well.
