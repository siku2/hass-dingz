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
   - Use a password WITHOUT special characters. The reason is simply because special characters need to be URL-escaped later on. If you know what you're doing, feel free to ignore this :P
   - Activate "Can only log in from the local network" switch.

> [!NOTE]
> You can use the same user for all your dingz devices. Don't create a new one per device, it doesn't improve security and only adds clutter.

### Set up your dingz devices to connect to the broker

We're almost there, the only thing left is to actually configure the dingz device(s) to connect to the broker.

1. Open the "Device Info" page of your dingz device: [![Open your Home Assistant instance and show the dingz integration.](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/integration/?domain=dingz)
2. Scroll down to the "Configuration" section where you should see a switch "MQTT Enable" and a text box "MQTT URI".
3. Start by filling the MQTT URI with `mqtt://username:password@homeassistant.local` and replace 'username' and 'password' with the credentials of the user we created previously (**Don't remove the ':' in-between**).

   (If you didn't listen to my advice and your password contains special characters you need to use a tool like [this](https://www.utilities-online.info/urlencode) to escape them.)
4. Enable the "MQTT Enable" switch.
5. If you scroll down to the "Diagnostic" section you should see a binary sensor called "MQTT". If everything is working, it will show "Connected". If it's still showing as "Disconnected" double check the URI and that the enable switch is turned on. If that doesn't help, try the steps outlined in [Debugging](#debugging).
6. Press the "Save Default Config" button to ensure these settings are preserved when the dingz restarts.
7. Go back to the integration overview page and reload the integration entry (alternatively you can also restart the Home Assistant). The integration will now provide more entities.

> [!IMPORTANT]
> I don't actually know whether dingz devices are able to resolve mDNS names (like `homeassistant.local`).
> If your device doesn't connect to the Home Assistant, try replacing `homeassistant.local` with the actual IP address of your Home Assistant instance.
>
> I also haven't tried to set up a TLS connection using the "Server Certificate" text box. I don't even know what format it expects (hopefully PEM, but maybe it uses raw DER which wouldn't work).
> If you're playing around with this, please open a new discussion.

## Debugging

If your dingz devices aren't showing up as connected on your Home Assistant there's no easy way to tell what went wrong.
At this point you should download [MQTTX](https://mqttx.app).

Start by connecting to the broker by using the same credentials as the dingz. If that doesn't work then you need to double check your username and password. Re-create the user and try again.

If you're able to connect you should immediately receive a bunch of messages where the topic starts with "dingz/".
If not, that means your dingz aren't connected. Double-check the configuration page to make sure they're correct. Try restarting the dingz as well.

Don't hesitate to create a new issue or start a discussion if thigns aren't working correctly.
