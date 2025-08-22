# buttplug_controller.py (Updated for buttplug-py v3)
import asyncio
import threading
import time
from typing import Optional, Dict, Any

try:
    # Import from the installed buttplug-py package
    from buttplug import (
        Client,
        WebsocketConnector,
        ProtocolSpec,
        ButtplugError,
        ClientError,
        ConnectorError,
        ServerError
    )

except ImportError as e:
    raise ImportError(
        "Could not import from 'buttplug'. Please ensure you have the correct version installed.\n"
        "Try: pip install buttplug-py"
    ) from e

class ButtplugController:
    def __init__(self, server_uri: str = "ws://127.0.0.1:12345"):
        """Initialize the Buttplug controller.
        
        Args:
            server_uri: WebSocket URI of the Intiface/Buttplug server
        """
        self.server_uri = server_uri
        self.client = Client("StrokeGPT Client")
        self.device = None
        self._lock = threading.Lock()  # Thread safety for device access
        self._connected = False  # Track connection state
        self._shutting_down = False  # Flag for graceful shutdown

        # Actuator references (Protocol v3)
        self._vibrator_actuators = []
        self._linear_actuators = []
        self._rotatory_actuators = []

        # State variables for the UI
        self.last_relative_speed = 0  # 0-100 scale for UI
        self.last_depth_pos = 50      # 0-100 scale for UI
        self.last_stroke_speed = 0    # Alias for last_relative_speed for compatibility
        
        # Continuous movement state
        self._target_speed = 0
        self._target_depth = 50
        self._target_range = 50
        self._movement_active = False
        
        # Setup async event loop in a background thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self._run_event_loop, 
            daemon=True,
            name="ButtplugControllerThread"
        )
        self.thread.start()
        
        # Start the continuous movement loop
        self._start_movement_loop()
        
        print("Buttplug Controller initialized. Waiting for connection...")

    def _run_event_loop(self):
        """Runs the asyncio event loop in its own thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _start_movement_loop(self):
        """Start the continuous movement loop."""
        async def movement_loop():
            """Continuous movement loop that runs in the background."""
            pos1 = 0.25  # Default positions
            pos2 = 0.75
            current_pos = pos1
            
            while not self._shutting_down:
                try:
                    # Check if we should be moving
                    if self._movement_active and self.is_connected and self.device:
                        # Update positions based on current targets
                        center_pos = max(0.0, min(1.0, self._target_depth / 100.0))
                        half_range = max(0.0, min(0.5, (self._target_range / 100.0) / 2.0))
                        pos1 = max(0.0, center_pos - half_range)
                        pos2 = min(1.0, center_pos + half_range)
                        
                        # Calculate duration based on speed (inverse relationship)
                        min_duration = 200  # ms
                        max_duration = 2000  # ms
                        duration_ms = int(max_duration - (max_duration - min_duration) * (self._target_speed / 100.0))
                        
                        # Determine next position
                        if current_pos == pos1:
                            next_pos = pos2
                        else:
                            next_pos = pos1
                            
                        current_pos = next_pos
                        
                        # Execute movement on all linear actuators
                        if self._linear_actuators:
                            for actuator in self._linear_actuators:
                                await actuator.command(duration_ms, current_pos)
                            await asyncio.sleep(duration_ms / 1000.0)
                            
                        # For vibrator actuators, just maintain continuous vibration
                        elif self._vibrator_actuators:
                            level = min(1.0, max(0.0, self._target_speed / 100.0))
                            for actuator in self._vibrator_actuators:
                                await actuator.command(level)
                            await asyncio.sleep(0.1)  # Small delay for continuous vibration
                            
                        # For rotatory actuators, just maintain continuous rotation
                        elif self._rotatory_actuators:
                            speed_level = min(1.0, max(0.0, self._target_speed / 100.0))
                            for actuator in self._rotatory_actuators:
                                await actuator.command(speed_level, True)  # clockwise
                            await asyncio.sleep(0.1)  # Small delay for continuous rotation
                        else:
                            # No compatible actuators, small delay to prevent busy loop
                            await asyncio.sleep(0.1)
                    else:
                        # Not moving, small delay to prevent busy loop
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    print(f"Error in movement loop: {e}")
                    await asyncio.sleep(1)  # Longer delay on error
        
        # Start the movement loop
        asyncio.run_coroutine_threadsafe(movement_loop(), self.loop)

    async def _connect_and_scan(self):
        """The core async connection and scanning logic."""
        try:
            # Connect to the server
            connector = WebsocketConnector(self.server_uri)
            await self.client.connect(connector)
            self._connected = True
            print("Successfully connected to Buttplug server.")
            
            # Start scanning for devices
            print("Scanning for devices...")
            await self.client.start_scanning()
            await asyncio.sleep(5)  # Wait for devices to be discovered
            await self.client.stop_scanning()
            
            # If we don't have a device yet, try to find one
            if not self.device:
                devices = self.client.devices
                print(f"Found {len(devices)} device(s)")
                
                for dev in devices.values():
                    if await self._try_use_device(dev):
                        break
                
                if not self.device:
                    print("No compatible devices found. Please ensure your device is connected and paired.")
        
        except ButtplugError as e:
            # Handle Buttplug-specific errors
            error_msg = str(e) if hasattr(e, '__str__') else repr(e)
            print(f"Buttplug error: {error_msg}")
            self._connected = False
        except Exception as e:
            # Handle all other exceptions
            error_msg = str(e) if hasattr(e, '__str__') else repr(e)
            print(f"Error in connection/scanning: {error_msg}")
            self._connected = False
    
    async def _try_use_device(self, device) -> bool:
        """Try to use a device if it's compatible.
        
        This method checks if a device has actuators we can use and categorizes them
        by their type (vibrator, linear, rotatory). It's important to note that in
        Buttplug protocol v3, devices may expose actuators in two ways:
        1. Through the generic `device.actuators` list
        2. Through specific attributes like `device.linear_actuators`
        
        We check both to ensure compatibility with different device implementations.
        """
        try:
            # Check if device has any actuators we can use (Protocol v3 approach)
            # Store references to specific actuator types for later use
            self._vibrator_actuators = []
            self._linear_actuators = []
            self._rotatory_actuators = []
            
            print(f"Checking device: {device.name}")
            print(f"Device has {len(device.actuators)} actuators")
            
            # Also check the specific actuator attributes
            # Some devices expose actuators through specific attributes rather than
            # the generic actuators list, so we check both for compatibility
            print(f"Device linear_actuators: {len(device.linear_actuators) if hasattr(device, 'linear_actuators') else 'N/A'}")
            print(f"Device rotatory_actuators: {len(device.rotatory_actuators) if hasattr(device, 'rotatory_actuators') else 'N/A'}")
            
            # Iterate through all actuators to identify their types
            # We check the description of each actuator to determine its type
            # This is the recommended approach in Buttplug protocol v3
            for actuator in device.actuators:
                # For debugging, let's see what actuator types we have
                print(f"  Actuator {actuator.index}: {actuator.description}")
                
                # Categorize actuators by their description
                desc = actuator.description.lower()
                if 'vibrate' in desc:
                    self._vibrator_actuators.append(actuator)
                elif 'linear' in desc:
                    self._linear_actuators.append(actuator)
                elif 'rotate' in desc:
                    self._rotatory_actuators.append(actuator)
            
            # Also check the specific actuator collections
            # Some devices expose actuators through specific attributes rather than
            # the generic actuators list, so we check both for maximum compatibility
            if hasattr(device, 'linear_actuators') and device.linear_actuators:
                print(f"  Adding {len(device.linear_actuators)} linear actuators from device.linear_actuators")
                self._linear_actuators.extend(device.linear_actuators)
                
            if hasattr(device, 'rotatory_actuators') and device.rotatory_actuators:
                print(f"  Adding {len(device.rotatory_actuators)} rotatory actuators from device.rotatory_actuators")
                self._rotatory_actuators.extend(device.rotatory_actuators)
            
            # Check if we found any compatible actuators
            if self._vibrator_actuators or self._linear_actuators or self._rotatory_actuators:
                with self._lock:
                    self.device = device
                    self.last_relative_speed = 0
                    self.last_stroke_speed = 0
                    self.last_depth_pos = 50
                print(f"Using device: {device.name}")
                print(f"  Found {len(self._vibrator_actuators)} vibrator actuators")
                print(f"  Found {len(self._linear_actuators)} linear actuators")
                print(f"  Found {len(self._rotatory_actuators)} rotatory actuators")
                return True
            else:
                print(f"No compatible actuators found for device: {device.name}")
        except Exception as e:
            print(f"Error checking device {device.name}: {e}")
            import traceback
            traceback.print_exc()
        return False

    @property
    def is_connected(self) -> bool:
        """Return the connection status.
        
        This property checks both the internal _connected flag and verifies that
        we still have a valid device reference. It also ensures the device is
        still present in the client's device list to handle unexpected disconnections.
        
        Returns:
            bool: True if connected to server and has an active device, False otherwise
        """
        if not self._connected or self._shutting_down:
            return False
            
        try:
            # Check if we have a valid device reference
            with self._lock:
                has_device = self.device is not None
                
            # If we think we have a device but it's not in the client's device list anymore
            if has_device and self.client and hasattr(self.client, 'devices') and self.device not in self.client.devices.values():
                with self._lock:
                    self.device = None
                return False
                
            return has_device
            
        except Exception as e:
            print(f"⚠️ Error checking connection status: {e}")
            return False

    def connect(self):
        """Starts the connection process in a non-blocking way."""
        print("Starting Buttplug connection process...")
        if self._shutting_down:
            print("Cannot connect while shutting down")
            return
            
        self._connected = False
        try:
            # Run the connection in a thread-safe way
            future = asyncio.run_coroutine_threadsafe(
                self._connect_and_scan(), 
                self.loop
            )
            # Wait up to 10 seconds for connection
            future.result(timeout=10)
            print("Buttplug connection process completed")
        except asyncio.TimeoutError:
            print("Connection attempt timed out")
            self._connected = False
        except Exception as e:
            error_msg = str(e) if hasattr(e, '__str__') else repr(e)
            print(f"Error during connection: {error_msg}")
            self._connected = False

    def move(self, speed: float, depth: float, stroke_range: float):
        """
        Set continuous movement parameters.
        
        This method updates the target parameters for continuous movement.
        The actual movement is handled by a background loop that continuously
        moves the device according to these parameters.
        
        Args:
            speed: Movement speed (0-100)
            depth: Center position of the movement (0-100)
            stroke_range: Range of the movement (0-100)
        """
        if not self.is_connected or not self.device:
            print("Cannot move: No device connected")
            return
            
        # Update UI state
        with self._lock:
            self.last_relative_speed = speed
            self.last_stroke_speed = speed  # Keep in sync for compatibility
            self.last_depth_pos = depth

        # Update target parameters for continuous movement
        self._target_speed = speed
        self._target_depth = depth
        self._target_range = stroke_range
        
        # Activate movement if not already active
        if speed > 0:
            self._movement_active = True
        else:
            self._movement_active = False
            # Stop the device
            self.stop()

    def test_movement(self):
        """Test device movement with a simple pattern."""
        if not self.is_connected:
            print("⚠️ Device not connected")
            return
            
        print("Testing device movement...")
        try:
            # Test vibration
            if self._vibrator_actuators:
                print("Testing vibration...")
                self.move(50, 50, 50)  # Medium speed, center depth, medium range
                time.sleep(3)
                self.stop()
                print("Vibration test completed")
                
            # Test linear movement
            elif self._linear_actuators:
                print("Testing linear movement...")
                self.move(30, 50, 50)  # Slow speed, center depth, medium range
                time.sleep(3)
                self.stop()
                print("Linear movement test completed")
                
            # Test rotation
            elif self._rotatory_actuators:
                print("Testing rotation...")
                self.move(50, 50, 50)  # Medium speed
                time.sleep(3)
                self.stop()
                print("Rotation test completed")
                
            else:
                print("No compatible actuators found for testing")
                
        except Exception as e:
            print(f"Error during movement test: {e}")
            import traceback
            traceback.print_exc()

    def stop(self):
        """Stop all device movements.
        
        This method stops continuous movement by setting the movement active flag to False
        and sending stop commands to all actuators.
        """
        if not self.is_connected or not self.device:
            print("Cannot stop: No device connected")
            return
            
        # Deactivate continuous movement
        self._movement_active = False
        
        async def do_stop():
            try:
                print("Stopping all device movements...")
                
                # Stop vibrator actuators
                for actuator in self._vibrator_actuators:
                    print(f"  Stopping vibrator actuator {actuator.index}")
                    await actuator.command(0.0)
                
                # Stop linear actuators (move to center position)
                for actuator in self._linear_actuators:
                    print(f"  Stopping linear actuator {actuator.index}")
                    await actuator.command(500, 0.5)  # 500ms duration, center position
                
                # Stop rotatory actuators
                for actuator in self._rotatory_actuators:
                    print(f"  Stopping rotatory actuator {actuator.index}")
                    await actuator.command(0.0, True)  # Stop rotation
                    
                # Update UI state
                with self._lock:
                    self.last_relative_speed = 0
                    self.last_stroke_speed = 0
                    
                print("All device movements stopped")
            except Exception as e:
                error_msg = str(e) if hasattr(e, '__str__') else repr(e)
                print(f"Error during stop: {error_msg}")
                raise
        
        try:
            # Execute the stop with a timeout
            future = asyncio.run_coroutine_threadsafe(do_stop(), self.loop)
            future.result(timeout=5.0)  # 5 second timeout for the stop
        except asyncio.TimeoutError:
            print("Stop command timed out")
        except Exception as e:
            error_msg = str(e) if hasattr(e, '__str__') else repr(e)
            print(f"Error executing stop: {error_msg}")

    def disconnect(self):
        """Gracefully disconnects from the server and cleans up resources."""
        if self._shutting_down:
            return
            
        print("Disconnecting from Buttplug server...")
        self._shutting_down = True
        
        try:
            # Stop any ongoing operations
            self.stop()
            
            # Create the async disconnect task
            async def do_disconnect():
                try:
                    # Disconnect the client if connected
                    if self._connected and hasattr(self.client, 'disconnect'):
                        await self.client.disconnect()
                        print("Client disconnected from server.")
                    
                    # Clear device reference and actuator lists
                    with self._lock:
                        self.device = None
                        self._vibrator_actuators = []
                        self._linear_actuators = []
                        self._rotatory_actuators = []
                    
                    # Stop the event loop
                    if hasattr(self, 'loop') and self.loop.is_running():
                        self.loop.stop()
                        
                except Exception as e:
                    error_msg = str(e) if hasattr(e, '__str__') else repr(e)
                    print(f"Error during disconnect: {error_msg}")
                    raise
            
            # Execute the disconnect with a timeout
            future = asyncio.run_coroutine_threadsafe(do_disconnect(), self.loop)
            future.result(timeout=5.0)  # 5 second timeout for disconnect
            
        except asyncio.TimeoutError:
            print("Disconnect timed out, forcing cleanup...")
        except Exception as e:
            error_msg = str(e) if hasattr(e, '__str__') else repr(e)
            print(f"Error during disconnect: {error_msg}")
        finally:
            # Ensure we clean up even if something went wrong
            try:
                # Stop the event loop if it's still running
                if hasattr(self, 'loop') and self.loop.is_running():
                    self.loop.call_soon_threadsafe(self.loop.stop)
                
                # Wait for the thread to finish (with a timeout)
                if hasattr(self, 'thread') and self.thread.is_alive():
                    self.thread.join(timeout=2.0)
                    
                # Final cleanup
                self._connected = False
                with self._lock:
                    self.device = None
                    self._vibrator_actuators = []
                    self._linear_actuators = []
                    self._rotatory_actuators = []
                
                print("Cleanup complete.")
                
            except Exception as e:
                error_msg = str(e) if hasattr(e, '__str__') else repr(e)
                print(f"Error during cleanup: {error_msg}")
            finally:
                self._shutting_down = False