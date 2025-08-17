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
        
        # Setup async event loop in a background thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self._run_event_loop, 
            daemon=True,
            name="ButtplugControllerThread"
        )
        self.thread.start()
        print("🤖 Buttplug Controller initialized. Waiting for connection...")

    def _run_event_loop(self):
        """Runs the asyncio event loop in its own thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect_and_scan(self):
        """The core async connection and scanning logic."""
        try:
            # Connect to the server
            connector = WebsocketConnector(self.server_uri)
            await self.client.connect(connector)
            self._connected = True
            print("✅ Successfully connected to Buttplug server.")
            
            # Start scanning for devices
            print("🔍 Scanning for devices...")
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
                    print("⚠️ No compatible devices found. Please ensure your device is connected and paired.")
        
        except ButtplugError as e:
            print(f"❌ Buttplug error: {e}")
            self._connected = False
        except Exception as e:
            print(f"🔥 Error in connection/scanning: {e}")
            self._connected = False
    
    async def _try_use_device(self, device) -> bool:
        """Try to use a device if it's compatible."""
        try:
            # Check if device has any actuators we can use (Protocol v3 approach)
            # Store references to specific actuator types for later use
            self._vibrator_actuators = []
            self._linear_actuators = []
            self._rotatory_actuators = []
            
            # Iterate through all actuators to identify their types
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
            
            # Check if we found any compatible actuators
            if self._vibrator_actuators or self._linear_actuators or self._rotatory_actuators:
                with self._lock:
                    self.device = device
                    self.last_relative_speed = 0
                    self.last_stroke_speed = 0
                    self.last_depth_pos = 50
                print(f"✅ Using device: {device.name}")
                print(f"  Found {len(self._vibrator_actuators)} vibrator actuators")
                print(f"  Found {len(self._linear_actuators)} linear actuators")
                print(f"  Found {len(self._rotatory_actuators)} rotatory actuators")
                return True
        except Exception as e:
            print(f"⚠️ Error checking device {device.name}: {e}")
        return False

    @property
    def is_connected(self) -> bool:
        """Return the connection status.
        
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
        if self._shutting_down:
            print("⚠️ Cannot connect while shutting down")
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
        except asyncio.TimeoutError:
            print("⚠️ Connection attempt timed out")
            self._connected = False
        except Exception as e:
            print(f"🔥 Error during connection: {e}")
            self._connected = False

    def move(self, speed: float, depth: float, stroke_range: float):
        """
        Executes a movement command with the given parameters.
        
        Args:
            speed: Movement speed (0-100)
            depth: Center position of the movement (0-100)
            stroke_range: Range of the movement (0-100)
        """
        if not self.is_connected or not self.device:
            print("⚠️ Cannot move: No device connected")
            return
            
        # Update UI state
        with self._lock:
            self.last_relative_speed = speed
            self.last_stroke_speed = speed  # Keep in sync for compatibility
            self.last_depth_pos = depth

        # Stop command
        if speed is None or speed <= 0:
            self.stop()
            return
            
        if depth is None or stroke_range is None:
            return

        async def do_move():
            try:
                # Use Protocol v3 actuator objects for device control
                if self._linear_actuators:
                    # Convert UI values to device-specific values
                    center_pos = max(0.0, min(1.0, depth / 100.0))
                    half_range = max(0.0, min(0.5, (stroke_range / 100.0) / 2.0))
                    
                    # Calculate positions
                    pos1 = max(0.0, center_pos - half_range)
                    pos2 = min(1.0, center_pos + half_range)
                    
                    # Calculate duration based on speed (inverse relationship)
                    min_duration = 200  # ms
                    max_duration = 2000  # ms
                    duration_ms = int(max_duration - (max_duration - min_duration) * (speed / 100.0))
                    
                    # Execute movement on all linear actuators
                    for actuator in self._linear_actuators:
                        await actuator.command(duration_ms, pos1)
                    await asyncio.sleep(duration_ms / 1000.0)
                    for actuator in self._linear_actuators:
                        await actuator.command(duration_ms, pos2)
                    await asyncio.sleep(duration_ms / 1000.0)
                    
                elif self._vibrator_actuators:
                    # Simple vibration based on speed
                    level = min(1.0, max(0.0, speed / 100.0))
                    
                    # Execute vibration on all vibrator actuators
                    for actuator in self._vibrator_actuators:
                        await actuator.command(level)
                        
                elif self._rotatory_actuators:
                    # For rotating devices, use speed for rotation speed
                    speed_level = min(1.0, max(0.0, speed / 100.0))
                    
                    # Execute rotation on all rotatory actuators
                    for actuator in self._rotatory_actuators:
                        await actuator.command(speed_level, True)  # clockwise
                    
            except Exception as e:
                print(f"⚠️ Error during move: {e}")
                raise
        
        try:
            # Execute the movement with a timeout
            future = asyncio.run_coroutine_threadsafe(do_move(), self.loop)
            future.result(timeout=5.0)  # 5 second timeout for the move
        except asyncio.TimeoutError:
            print("⚠️ Move command timed out")
            self.stop()
        except Exception as e:
            print(f"🔥 Error executing move: {e}")

    def stop(self):
        """Stop all device movement."""
        if not self.device:
            return
            
        print("⏹️ Stopping device...")
        
        async def do_stop():
            try:
                # Use Protocol v3 actuator objects for stopping device
                # Send stop commands to all actuators
                for actuator in self._vibrator_actuators:
                    await actuator.command(0.0)
                for actuator in self._linear_actuators:
                    await actuator.command(100, 0.5)  # Move to center position with short duration
                for actuator in self._rotatory_actuators:
                    await actuator.command(0.0, True)  # Stop rotation
            except Exception as e:
                print(f"⚠️ Error during stop: {e}")
                raise
        
        try:
            future = asyncio.run_coroutine_threadsafe(do_stop(), self.loop)
            future.result(timeout=2.0)  # 2 second timeout for stop
            print("✅ Device stopped")
        except asyncio.TimeoutError:
            print("⚠️ Stop command timed out")
        except Exception as e:
            print(f"🔥 Error stopping device: {e}")
        finally:
            # Update UI state
            with self._lock:
                self.last_relative_speed = 0
                self.last_stroke_speed = 0

    def disconnect(self):
        """Gracefully disconnects from the server and cleans up resources."""
        if self._shutting_down:
            return
            
        print("🔌 Disconnecting from Buttplug server...")
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
                        print("✅ Client disconnected from server.")
                    
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
                    print(f"⚠️ Error during disconnect: {e}")
                    raise
            
            # Execute the disconnect with a timeout
            future = asyncio.run_coroutine_threadsafe(do_disconnect(), self.loop)
            future.result(timeout=5.0)  # 5 second timeout for disconnect
            
        except asyncio.TimeoutError:
            print("⚠️ Disconnect timed out, forcing cleanup...")
        except Exception as e:
            print(f"🔥 Error during disconnect: {e}")
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
                
                print("✅ Cleanup complete.")
                
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")
            finally:
                self._shutting_down = False