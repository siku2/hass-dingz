# Dingz Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/siku2/hass-dingz.svg?style=for-the-badge)](https://github.com/siku2/hass-dingz/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/siku2/hass-dingz.svg?style=for-the-badge)](https://github.com/siku2/hass-dingz/commits/main)
[![License](https://img.shields.io/github/license/siku2/hass-dingz.svg?style=for-the-badge)](LICENSE)

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/docs/faq/custom_repositories)

[![GitLocalize](https://gitlocalize.com/repo/8874/whole_project/badge.svg)](https://gitlocalize.com/repo/8874/whole_project?utm_source=badge)

_Integration to integrate with [Dingz](https://www.dingz.ch) devices._

## Installation

1. Add this repository as a custom repository to HACS: [![Add Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=siku2&repository=hass-dingz&category=integration)
2. Use HACS to install the integration.
3. Restart Home Assistant.
4. Set up the integration using the UI: [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dingz)
5. **(optional but recommended)** Set up the MQTT connection from dingz to Home Assistant. [Read the Guide][MQTT Guide]

## Supported Features

When you make changes to the dingz configuration (for instance when setting up the MQTT connection, or changing the output configuration), reload the integration (or restart Home Assistant) to update the entities.

The following features are fully supported and, since I'm actively using them, should always work:

- Light outputs (including dimmers)
- Front panel LED with RGB support
- PIR Motion detection (incl. live updates when used in combination with MQTT[^1])
- Button press events (**only** when used in combination with MQTT[^1])
- Power and Energy sensors for outputs
- Various other sensors like brightness, temperature etc.
- Physical dingz inputs (incl. live updates when used in combination with MQTT[^1])

The following features have been implemented, but since I'm not actively using these configurations, I don't know how well they work.

- Blinds / Motors (incl. live updates when used in combination with MQTT[^1])
- Thermostats (exposed as climate entites in Home Assistant)
- Fan outputs

> [!NOTE]
> If you're using one of these, be sure to contact me (open an issue or a new discussion). With a bit of help, I can easily improve the integration.
> This also applies to unimplemented features, of course.

And now for the list of things that **won't** be implemented:

- Dingz firmware updates through Home Assistant. As far as I can tell the dingz doesn't know itself, whether an update is available. They are performed by the mobile app by downloading the firmware blob from somewhere. I'm not planning on reverse engineering this at the moment. Don't hesitate to let me know if you have more information about this though.

[^1]: See the [MQTT Guide].

## Contributions are welcome

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

### Providing translations for other languages

If you would like to use the integration in another language, you can help out by providing the necessary translations.

[Head over to **GitLocalize** to start translating.](https://gitlocalize.com/repo/8874)

If your desired language isn't available there, just open an issue to request it.

You can also just do the translations manually in [custom_components/dingz/translations/](./custom_components/dingz/translations/) and open a pull request with the changes.

<!--  -->

[MQTT Guide]: https://github.com/siku2/hass-dingz/blob/main/docs/mqtt.md
