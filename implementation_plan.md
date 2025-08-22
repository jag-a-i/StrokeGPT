# Implementation Plan: Port Buttplug Functionality to StrokeGPT 2.0

## Overview
Port Buttplug functionality from StrokeGPT 1.x to 2.0 by integrating the existing ButtplugController while adapting it to the new modular architecture and enhanced LLM context system. This involves adding WebSocket-based device control for Buttplug.io compatible devices while maintaining compatibility with the existing Handy controller system.

## Types
Define interfaces and data structures for Buttplug device integration:

```python
# Buttplug device interface
class ButtplugDevice:
    index: int
    name: str
    actuators: int
    linear_actuators: List[int]
    rotatory_actuators: List[int]
    vibrator_actuators: List[int]

# Connection configuration
class ButtplugConnectionConfig:
    server_uri: str = "ws://127.0.0.1:12345"
    auto_scan: bool = True
    device_filter: Optional[List[str]] = None
    connection_timeout: int = 10
    retry_attempts: int = 3

# Controller state tracking
class ButtplugControllerState:
    is_connected: bool = False
    server_connected: bool = False
    device_connected: bool = False
    current_device: Optional[ButtplugDevice] = None
    available_devices: List[ButtplugDevice] = []
    last_speed: int = 0
    last_depth: int = 50
    last_range: int = 50
    connection_errors: List[str] = []
```

## Files

### New Files to Create
- `buttplug_controller.py` - Main Buttplug controller class with WebSocket connection handling
- `buttplug_integration.py` - Integration layer adapting 1.x controller to 2.0 architecture
- `buttplug_device_manager.py` - Device discovery, filtering, and management
- `tests/test_buttplug_controller.py` - Unit tests for controller functionality
- `tests/test_buttplug_integration.py` - Integration tests
- `static/js/buttplug_ui.js` - Frontend JavaScript for Buttplug connection UI

### Existing Files to Modify
- `app.py` - Add Buttplug routes and controller initialization
- `settings_manager.py` - Add Buttplug configuration settings
- `requirements.txt` - Add buttplug-py dependency
- `background_modes.py` - Update AutoModeThread to support Buttplug devices
- `index.html` - Add Buttplug connection interface
- `static/css/styles.css` - Add Buttplug-specific styling

### Configuration Files
- `my_settings.json` - Add Buttplug server URI and device settings

## Functions

### New Functions
- `ButtplugController.__init__(server_uri: str = "ws://127.0.0.1:12345")` - Initialize controller with WebSocket URI
- `ButtplugController.connect() -> bool` - Establish connection to Intiface server
- `ButtplugController.scan_devices() -> List[ButtplugDevice]` - Discover and list available devices
- `ButtplugController.select_device(device_index: int) -> bool` - Select specific device for control
- `ButtplugController.move(speed: int, depth: int, stroke_range: int, context: dict = None)` - Control device movement
- `ButtplugController.stop()` - Stop all device movement immediately
- `ButtplugController.disconnect()` - Clean shutdown and resource cleanup
- `ButtplugController.get_device_info() -> dict` - Get current device information
- `ButtplugController.test_connection() -> bool` - Test server connectivity

### Modified Functions
- `get_current_context()` - Include Buttplug device state and available devices
- `start_background_mode()` - Pass Buttplug controller to background threads
- `enforce_move()` - Apply movement constraints for Buttplug devices
- `add_message_to_queue()` - Add device-specific status messages

## Classes

### New Classes
- `ButtplugController` - Main controller class for WebSocket communication
- `ButtplugDeviceManager` - Device discovery and management wrapper
- `ButtplugIntegration` - 2.0 architecture integration layer
- `ButtplugErrorHandler` - Centralized error handling and logging

### Modified Classes
- `SettingsManager` - Add Buttplug-specific configuration methods
- `AutoModeThread` - Support both Handy and Buttplug controllers
- `LLMService` - Enhanced context with device capabilities

## Dependencies

### New Dependencies
- `buttplug-py>=0.2.0` - Buttplug Python client library
- `websockets>=10.0` - WebSocket support for async communication
- `asyncio` - Async support (Python standard library)

### Updated Dependencies
- Ensure Flask and requests compatibility with new async operations

## Testing

### Test Categories
- **Unit Tests**: Individual function and method testing
- **Integration Tests**: WebSocket communication and device control
- **UI Tests**: Frontend JavaScript functionality
- **Background Mode Tests**: Auto, edging, and milking with Buttplug devices
- **Error Handling Tests**: Connection failures and device disconnection scenarios

### Test Files
- `tests/test_buttplug_controller.py` - Controller unit tests
- `tests/test_buttplug_integration.py` - Integration and UI tests
- `tests/test_buttplug_device_manager.py` - Device management tests
- `tests/test_buttplug_background_modes.py` - Background mode compatibility

## Implementation Order

1. **Setup Dependencies** - Update requirements.txt with buttplug-py
2. **Core Controller Port** - Port ButtplugController from 1.x with enhancements
3. **Settings Integration** - Add Buttplug settings to SettingsManager
4. **Flask Routes** - Add Buttplug connection and control endpoints
5. **UI Integration** - Add Buttplug connection interface to web UI
6. **Background Modes** - Update AutoModeThread for Buttplug support
7. **Context Integration** - Include Buttplug state in LLM context
8. **Device Management** - Add device discovery and filtering
9. **Testing** - Add comprehensive test coverage
10. **Documentation** - Update README and create setup guide

## Key Integration Points

### LLM Context Enhancement
The 2.0 version provides enhanced context to the LLM. Buttplug device information will be included:
- Available devices and capabilities
- Current device state (speed, depth, connection status)
- Device-specific constraints and features
- Error states and connection issues

### Script Library Integration
The 2.0 version includes a script library system. Buttplug functionality will:
- Record and replay device movements as scripts
- Convert existing Handy scripts for Buttplug devices where possible
- Store device-specific movement patterns
- Support script sharing between device types

### Error Handling and Resilience
Enhanced error handling compared to 1.x:
- Graceful fallback when devices disconnect
- Connection retry logic with exponential backoff
- Device capability detection and feature adaptation
- Comprehensive logging for debugging

### Multi-Device Support
Building on 1.x's device abstraction:
- Seamless switching between Handy and Buttplug devices
- Device preference and auto-selection logic
- Simultaneous multi-device support (future enhancement)
- Device capability comparison and recommendation

### Performance Considerations
- Async WebSocket operations to prevent UI blocking
- Efficient device state polling and updates
- Background thread management for continuous operation
- Memory usage optimization for long-running sessions
