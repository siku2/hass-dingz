# Dingz Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/siku2/hass-dingz.svg?style=for-the-badge)](https://github.com/siku2/hass-dingz/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/siku2/hass-dingz.svg?style=for-the-badge)](https://github.com/siku2/hass-dingz/commits/main)
[![License](https://img.shields.io/github/license/siku2/hass-dingz.svg?style=for-the-badge)](LICENSE)

[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/docs/faq/custom_repositories)

_Integration to integrate with [Dingz](https://www.dingz.ch) devices._


## Installation

1. Add this repository as a custom repository to HACS: <https://hacs.xyz/docs/faq/custom_repositories>
2. Use HACS to install the integration.
3. Restart Home Assistant.
4. Set up the integration using the UI: [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dingz)


## Supported Features

When you make changes to the dingz configuration (for instance when setting up the MQTT connection, or changing the output configuration), reload the integration (or restart Home Assistant) to update the entities.

The following features are fully supported and, since I'm actively using them, should always work:

- Light outputs (including dimmers)
- Front panel LED with RGB support
- PIR Motion detection (incl. live updates when used in combination with MQTT)
- Button press events (incl. live updates when used in combination with MQTT)
- Power and Energy sensors for outputs
- Various other sensors like brightness, temperature etc.

The following features have been implemented, but since I'm not actively using these configurations, I don't know how well they work.

- Thermostats (exposed as climate entites in Home Assistant)
- Physical dingz inputs
- Blinds / Motors
- Fan outputs

> [!NOTE]
> If you're using one of these, be sure to contact me (open an issue or a new discussion). With a bit of help from your side, I can easily improve the integration.
> This also applies to unimplemented features, of course.

And now for the list of things that **won't** be implemented:

- Dingz firmware updates through Home Assistant. As far as I can tell the dingz doesn't know itself, whether an update is available. They are performed by the mobile app by downloading the firmware blob from somewhere. I'm not planning on reverse engineering this at the moment.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)
