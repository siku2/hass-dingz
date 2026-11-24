# MQTT

The dingz firmware has a somewhat hidden feature that allows it to connect to an [MQTT](https://mqtt.org) broker.

By default the integration uses polling to update the state of the dingz (i.e. it repeatedly requests the current state from the dingz), but by enabling MQTT the dingz device will actively push its current state to the Home Assistant.
This allows for updates to be performed faster and also enables additional features like detecting button presses that aren't available without MQTT.

## Using the Home Assistant Mosquitto Add-on

If you have access to Home Assistant Supervisor add-ons, the setup is quite straightforward and can be done with just the Home Assistant instance.

### Install the add-on and set up the MQTT integration for Home Assistant

1. Install the Mosquitto add-on: [![Open your Home Assistant instance and show the Mosquitto add-on.](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_mosquitto)
2. Activate "Start on boot" and then start the add-on. We don't need to make any changes to the configuration.
3. After a while, Home Assistant should automatically discover this broker. Set it up like a typical integration.

You now have an MQTT broker running on your Home Assistant, that devices in your local network can connect to, to communicate with each other or with Home Assistant.
The broker uses basic username and password authentication and re-uses the Home Assistant users database. This means that all your Home Assistant users will be able to connect to the broker with their credentials.

### Create a new user for the dingz devices to use

As explained above, the Mosquitto broker is set up to only allow Home Assistant users to connect. It's sensible to create a dedicated "headless" user for your dingz devices to connect with.

1. Go to your Home Assistant's "Users" configuration page: [![Open your Home Assistant instance and show your users.](https://my.home-assistant.io/badges/users.svg)](https://my.home-assistant.io/redirect/users/)
2. Create a new user.
   - I would recommend the username "dingz", but you're free to choose whatever. The display name isn't relevant, but my recommendation is to use a descriptive display name like "Dingz MQTT Connection" so you know why it's there.
   - Activate "Can only log in from the local network" switch.

> [!NOTE]
> You can use the same user for all your dingz devices. Don't create a new one per device, it doesn't improve security and only adds clutter.

### Set up your dingz devices to connect to the broker

We're almost there. The only thing left is to configure the dingz device(s) to connect to the broker.

1. Open the dingz integration: [![Open your Home Assistant instance and show the dingz integration.](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/integration/?domain=dingz)
2. Select the dingz entry and choose "Configure", then "MQTT connection".
3. Check the broker host and port. The form suggests the broker that Home Assistant uses.
4. Enter the username and password of the user we created previously.
5. Submit the form. The integration saves the settings on the dingz and reloads itself. It will now provide more entities.
6. In the "Diagnostic" section of the dingz device you should see a binary sensor called "MQTT". If everything works, it shows "Connected". If it still shows "Disconnected", check the settings in step 3 and 4. If that doesn't help, try the steps in [Debugging](#debugging).

> [!IMPORTANT]
> I don't know whether dingz devices can resolve mDNS names (like `homeassistant.local`).
> If your device doesn't connect to Home Assistant, use the IP address of your Home Assistant instance as the broker host.
>
> I also haven't tried to set up a TLS connection with the "Server certificate" field. I don't know what format the dingz expects (hopefully PEM).
> If you try this, please open a new discussion.

## Debugging

If your dingz devices aren't showing up as connected on your Home Assistant there's no easy way to tell what went wrong.
At this point you should download [MQTTX](https://mqttx.app).

Start by connecting to the broker by using the same credentials as the dingz. If that doesn't work then you need to double check your username and password. Re-create the user and try again.

If you're able to connect you should immediately receive a bunch of messages where the topic starts with "dingz/".
If not, that means your dingz aren't connected. Double-check the configuration page to make sure they're correct. Try restarting the dingz as well.

Don't hesitate to create a new issue or start a discussion if thigns aren't working correctly.
