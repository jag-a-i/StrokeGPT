# Buttplug Controller Documentation

## Overview

The `ButtplugController` class provides an interface for controlling intimate hardware devices through the Buttplug protocol. This implementation has been updated to fully comply with Buttplug Protocol v3, which uses an actuator-based approach rather than direct device methods.

## Key Features

- Asynchronous device control with thread safety
- Protocol v3 compliance with proper actuator handling
- Support for linear, vibration, and rotation actuators
- Automatic device discovery and connection
- Graceful error handling and resource cleanup

## Architecture

The controller uses a background thread to run an asyncio event loop, allowing for non-blocking device control while maintaining a synchronous interface for the main application.

### Main Components

1. **Client Management**: Handles connection to the Buttplug server
2. **Device Discovery**: Automatically scans and connects to compatible devices
3. **Actuator Control**: Manages different types of actuators (vibration, linear, rotation)
4. **State Management**: Tracks connection status and device state
5. **Thread Safety**: Uses locks to ensure safe access to shared resources

## Protocol v3 Implementation

### Actuator-Based Control

In Protocol v3, devices expose actuators rather than direct methods. The controller identifies and stores references to three types of actuators:

- **Vibrator Actuators**: Control vibration intensity (0.0-1.0)
- **Linear Actuators**: Control position and movement (duration, position)
- **Rotatory Actuators**: Control rotation speed and direction (speed, clockwise)

### Device Capability Detection

The `_try_use_device` method scans through `device.actuators` and categorizes them by their description:

```python
for actuator in device.actuators:
    desc = actuator.description.lower()
    if 'vibrate' in desc:
        self._vibrator_actuators.append(actuator)
    elif 'linear' in desc:
        self._linear_actuators.append(actuator)
    elif 'rotate' in desc:
        self._rotatory_actuators.append(actuator)
```

### Command Execution

Instead of calling methods directly on the device object, commands are sent to individual actuators:

```python
# For vibration
for actuator in self._vibrator_actuators:
    await actuator.command(level)

# For linear movement
for actuator in self._linear_actuators:
    await actuator.command(duration_ms, pos)

# For rotation
for actuator in self._rotatory_actuators:
    await actuator.command(speed, clockwise)
```

## API Reference

### Constructor

```python
ButtplugController(server_uri: str = "ws://127.0.0.1:12345")
```

Initializes the controller with the specified Buttplug server URI.

### Methods

#### `connect() -> None`

Starts the connection process to the Buttplug server and scans for devices.

#### `move(speed: float, depth: float, stroke_range: float) -> None`

Executes a movement command with the given parameters:
- `speed`: Movement speed (0-100)
- `depth`: Center position of the movement (0-100)
- `stroke_range`: Range of the movement (0-100)

#### `stop() -> None`

Stops all device movement by sending appropriate commands to all actuators.

#### `disconnect() -> None`

Gracefully disconnects from the server and cleans up resources.

#### `is_connected() -> bool`

Returns the connection status.

### Properties

- `last_relative_speed`: Last speed setting (0-100)
- `last_depth_pos`: Last depth position (0-100)
- `last_stroke_speed`: Alias for last_relative_speed

## Implementation Details

### Thread Safety

The controller uses a `threading.Lock` to ensure safe access to shared resources, particularly the device reference and actuator lists.

### Error Handling

The controller implements comprehensive error handling for:
- Connection failures
- Device communication errors
- Timeout conditions
- Unexpected exceptions

### Resource Cleanup

The controller ensures proper cleanup of resources:
- Stops device movement before disconnecting
- Clears device references and actuator lists
- Stops the asyncio event loop
- Joins background threads

## Usage Example

```python
# Initialize controller
controller = ButtplugController("ws://127.0.0.1:12345")

# Connect to server and devices
controller.connect()

# Check connection status
if controller.is_connected:
    # Move device
    controller.move(speed=50, depth=50, stroke_range=30)
    
    # Stop device
    controller.stop()

# Disconnect when finished
controller.disconnect()
```

## Troubleshooting

### Connection Issues

1. Ensure the Buttplug server (Intiface) is running
2. Verify the server URI is correct
3. Check that devices are properly paired with the server

### Device Not Detected

1. Ensure the device is powered on and paired
2. Check that the device is supported by the Buttplug protocol
3. Restart the scanning process

### Movement Not Working

1. Verify the device has the appropriate actuators
2. Check that actuator commands are being sent correctly
3. Ensure the device is not in a fault state

## Future Improvements

1. Add support for sensor feedback
2. Implement more sophisticated device control patterns
3. Add device-specific configuration options
4. Improve error reporting and logging