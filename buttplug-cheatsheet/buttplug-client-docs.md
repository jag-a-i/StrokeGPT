This document provides a comprehensive guide for developers using the `buttplug-py` library. This library allows Python applications to connect to a Buttplug server (like Intiface Central) and control a wide range of haptic devices.

## Getting Started: A Practical Example

The primary workflow involves creating a `Client`, connecting it to a server via a `WebsocketConnector`, scanning for devices, and then interacting with them. All interactions are asynchronous, so `async` and `await` are used extensively.

Here is a complete example that connects to a server, scans for devices for 5 seconds, and then vibrates the first available vibrator.

```python
import asyncio
from buttplug import Client, WebsocketConnector, ProtocolSpec

async def main():
    """
    The main function for the example.
    It creates a client, connects to a server, scans for devices,
    and controls the first vibrator found.
    """
    # Create a Client with a name and the desired Buttplug protocol version.
    # It's recommended to use the latest version (v3).
    client = Client("My Awesome App", ProtocolSpec.v3)
    
    # Instantiate a WebsocketConnector with the server's address.
    # The default for Intiface Central is "ws://127.0.0.1:12345".
    connector = WebsocketConnector("ws://127.0.0.1:12345")

    try:
        # Connect to the server. This is an awaitable coroutine.
        await client.connect(connector)
        print("Successfully connected to the Buttplug server.")

        # Start scanning for devices. This is also an awaitable coroutine.
        await client.start_scanning()
        print("Scanning for devices... (will stop after 5 seconds)")
        
        # Wait for a few seconds to allow devices to be discovered.
        await asyncio.sleep(5)
        
        # Stop scanning.
        await client.stop_scanning()
        print(f"Stopped scanning. Found {len(client.devices)} devices.")

        # If any devices were found, interact with them.
        if client.devices:
            # Select the first device.
            first_device = next(iter(client.devices.values()))
            print(f"Selected device: {first_device.name}")
            
            # Find the first vibrator (ScalarActuator of type 'Vibrate' in v3).
            vibrator = next(
                (
                    actuator
                    for actuator in first_device.actuators
                    if hasattr(actuator, 'type') and actuator.type == 'Vibrate'
                ),
                None,
            )

            if vibrator:
                print("Vibrating the first motor at 50% for 2 seconds...")
                # The command() method for a ScalarActuator takes a float from 0.0 to 1.0.
                await vibrator.command(0.5)
                await asyncio.sleep(2)
                
                print("Stopping vibration...")
                await vibrator.command(0.0)
            else:
                print("No vibrators found on the selected device.")

        else:
            print("No devices were found. Please ensure your devices are on and in pairing mode.")

    except Exception as e:
        # The library raises specific ButtplugError exceptions for different issues.
        print(f"An error occurred: {e}")
    finally:
        # Always ensure the client disconnects gracefully.
        if client.connected:
            await client.disconnect()
            print("Disconnected from the server.")

if __name__ == "__main__":
    asyncio.run(main())
```


## Core Concepts

The library's architecture is built around a few key classes that manage the connection, devices, and their capabilities.

### `Client`
The `Client` is the central hub of your application. It manages the connection state, handles message passing, and maintains a list of available devices.

*   `__init__(self, name: str, v: ProtocolSpec = ProtocolSpec.v3)`: When creating a client, you must provide a `name` for your application. You can also specify a Buttplug `ProtocolSpec` version, though it's best to default to the latest.
*   `devices` (property): A dictionary of `Device` objects currently connected to the server, keyed by their integer index.
*   `connect(connector)`: Asynchronously establishes the connection to the server using a provided `connector` object.
*   `start_scanning()`: Asynchronously tells the server to start looking for devices. The client's `devices` dictionary will be populated as devices are discovered.
*   `stop_scanning()`: Asynchronously tells the server to stop looking for new devices.
*   `disconnect()`: Asynchronously closes the connection to the server.
*   `stop_all()`: Immediately stops all activity on all connected devices.

### `WebsocketConnector`
This is the transport layer that connects your `Client` to the Buttplug server.

*   `__init__(self, address: str)`: Requires the WebSocket address of the server. The standard address for a local Intiface Central instance is `ws://127.0.0.1:12345`.

### `Device`
A `Device` object represents a physical piece of hardware. It provides access to the device's capabilities through its `actuators` and `sensors`.

*   `name` and `display_name` (properties): Identifiers for the device. `display_name` is often more user-friendly.
*   `index` (property): The unique integer ID assigned by the server.
*   `actuators` (property): A tuple of `Actuator` objects that can perform actions (e.g., vibrate, rotate, move linearly).
*   `sensors` (property): A tuple of `Sensor` objects that can read data (e.g., battery level, button presses).
*   `stop()`: Asynchronously sends a command to halt all actions on this specific device.

## Device Capabilities: Actuators and Sensors

Devices expose their functionality through `Actuator` and `Sensor` objects. The types of these objects and their methods depend on the Buttplug protocol version negotiated with the server. The library handles this translation for you.

### Actuators

Actuators are the parts of a device that *do* things. You interact with them using their `command()` method.

#### Protocol v3 (Recommended)
This is the most modern and standardized version.

*   `ScalarActuator`: The primary actuator type in v3. It controls a single value, typically from 0.0 to 1.0.
    *   `type` (property): A string indicating the function, such as `'Vibrate'`, `'Constrict'`, or `'Inflate'`.
    *   `command(scalar: float)`: Sets the actuator's intensity. For a vibrator, `0.5` would be 50% speed.
*   `LinearActuator`: Controls linear back-and-forth motion.
    *   `command(duration: int, position: float)`: Moves the actuator to a `position` (0.0 to 1.0) over a `duration` in milliseconds.
*   `RotatoryActuator`: Controls rotational motion.
    *   `command(speed: float, clockwise: bool)`: Rotates at a given `speed` (0.0 to 1.0) in the specified direction.

#### Older Protocols (v0, v1, v2)
The library provides backward compatibility. If connected to an older server, the `Device` object will be populated with older, more specific actuator types.

*   `VibrateActuator` (v1/v2): `command(speed: float)`
*   `SingleMotorVibrateActuator` (v0): `command(speed: float)`
*   And other device-specific actuators like `FleshlightLaunchFW12Actuator` (v0).

While these work, it is highly recommended to use a server that supports **protocol v3** for the most consistent and feature-rich experience.

### Sensors

Sensors are the parts of a device that *read* data.

#### Protocol v3
*   `GenericSensor`: Can read a value from the device.
    *   `type` (property): The type of data, e.g., `'Battery'`, `'Button'`, `'Pressure'`.
    *   `read()`: Asynchronously returns the sensor's current value(s) as a list of numbers.
*   `SubscribableSensor`: A sensor that can provide a continuous stream of data.
    *   `subscribe(callback)`: Begins listening for sensor data. The provided `callback` function will be called with a list of numbers each time the device sends an update.
    *   `unsubscribe()`: Stops listening.

#### Protocol v2
*   `BatteryLevel`: `read()` returns the battery level from 0.0 to 1.0.
*   `RSSILevel`: `read()` returns the signal strength.

## Error Handling

The library uses a set of custom exceptions, all inheriting from `ButtplugError`, to signal problems. It is crucial to wrap your connection and communication logic in `try...except` blocks.

*   **`ClientError`**: General errors originating from the client.
    *   `ScanNotRunningError`: Thrown if you call `stop_scanning()` without having called `start_scanning()` first.
    *   `UnsupportedCommandError`: The device does not support the action you tried to perform (e.g., calling `stop()` on a device without that capability).
*   **`ConnectorError`**: Errors related to the connection itself.
    *   `ServerNotFoundError`: Could not connect to the specified address. Ensure Intiface Central (or another Buttplug server) is running.
    *   `InvalidAddressError`: The WebSocket address format is incorrect.
    *   `DisconnectedError`: The connection was lost while trying to send a message.
*   **`ServerError`**: Errors reported by the Buttplug server in response to a command.
    *   `DeviceServerError`: A command sent to a device failed for a reason specific to the hardware.