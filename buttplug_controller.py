# buttplug_controller.py (Corrected "Execute-and-Wait" Implementation)
import asyncio
import threading
import time
from buttplug import Client, WebsocketConnector

class ButtplugController:
    def __init__(self, server_uri="ws://127.0.0.1:12345"):
        self.server_uri = server_uri
        self.client = Client("StrokeGPT Client")
        self.device = None
        self._lock = threading.Lock()  # Lock for accessing shared resources like the device

        # State variables for the UI. These are updated after each move.
        self.last_relative_speed = 0
        self.last_depth_pos = 50
        
        # --- Threading & AsyncIO Setup ---
        # The Buttplug library requires its own asyncio event loop to run persistently.
        # We run this loop in a dedicated background thread.
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        print("🤖 Buttplug Controller initialized. Waiting for connection...")

    def _run_event_loop(self):
        """Runs the asyncio event loop in its own thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect_and_scan(self):
        """The core async connection and scanning logic."""
        try:
            connector = WebsocketConnector(self.server_uri, loop=self.loop)
            await self.client.connect(connector)
            print("✅ Successfully connected to Buttplug server.")
            print("...Scanning for devices for 5 seconds...")
            await self.client.start_scanning()
            await asyncio.sleep(5)
            await self.client.stop_scanning()

            if not self.client.devices:
                print("⚠️ No devices found connected to Intiface/Buttplug server.")
                return

            # Find the first available compatible device
            found_device = next((dev for dev in self.client.devices.values() if "Linear" in dev.allowed_messages or "Vibrate" in dev.allowed_messages), None)
            
            if found_device:
                with self._lock:
                    self.device = found_device
                print(f"✅ Device Locked: {self.device.name}")
            else:
                print("⚠️ No compatible (Linear or Vibrate) devices were found.")

        except Exception as e:
            print(f"🔥 Error connecting to or scanning on Buttplug server: {e}")

    def connect(self):
        """Public method to trigger the connection process from the main app thread."""
        if self.client.is_connected:
            return
        # Safely submit the async connection task to the event loop thread
        asyncio.run_coroutine_threadsafe(self._connect_and_scan(), self.loop)

    def move(self, speed, depth, stroke_range):
        """
        Executes a SINGLE, COMPLETE move and waits for it to finish.
        This is a BLOCKING call from the perspective of the main application.
        """
        with self._lock:
            if not self.device:
                print("⚠️ Move called but no device is connected.")
                return
            
            # Update state for the UI before executing the move
            self.last_relative_speed = speed
            self.last_depth_pos = depth

        # A speed of 0 is a stop command
        if speed is None or speed == 0:
            self.stop()
            return
        if depth is None or stroke_range is None:
            return

        # Define the async task to be run
        async def do_move():
            # --- Linear Device Logic (Strokers) ---
            if "Linear" in self.device.allowed_messages:
                # Buttplug position is 0.0 (in) to 1.0 (out)
                center_pos = depth / 100.0
                half_range = (stroke_range / 100.0) / 2.0
                pos1 = max(0.0, center_pos - half_range)
                pos2 = min(1.0, center_pos + half_range)

                # Duration is the time for ONE half-stroke.
                # Higher speed means lower duration.
                max_duration_ms = 2000
                min_duration_ms = 200
                duration_ms = int(max_duration_ms - (max_duration_ms - min_duration_ms) * (speed / 100.0))
                
                # Execute one full stroke (out and back)
                await self.device.linear(duration_ms, pos1)
                await asyncio.sleep(duration_ms / 1000.0)
                await self.device.linear(duration_ms, pos2)
                await asyncio.sleep(duration_ms / 1000.0)

            # --- Vibrate Device Logic ---
            elif "Vibrate" in self.device.allowed_messages:
                vibration_level = speed / 100.0
                # Vibrate commands don't have a duration, they just set a level.
                # The "pause" will be handled by the sleep in background_modes.py
                await self.device.vibrate(vibration_level)
        
        try:
            # Submit the task to the event loop and WAIT for it to complete.
            # The timeout prevents the main app from freezing if the device hangs.
            future = asyncio.run_coroutine_threadsafe(do_move(), self.loop)
            future.result(timeout=5.0) # Wait up to 5 seconds for the move to finish
        except asyncio.TimeoutError:
            print("🔥 Warning: Device move command timed out.")
            self.stop()
        except Exception as e:
            print(f"🔥 An error occurred during the move command: {e}")

    def stop(self):
        """Stops all device movement."""
        with self._lock:
            if not self.device:
                return
        
        print("...Sending stop command...")
        async def do_stop():
            await self.device.stop()
        
        try:
            future = asyncio.run_coroutine_threadsafe(do_stop(), self.loop)
            future.result(timeout=2.0)
            print("✅ Device stop command sent.")
        except Exception as e:
            print(f"🔥 Error sending stop command: {e}")

    def disconnect(self):
        """Gracefully disconnects from the server and cleans up resources."""
        print("...Disconnecting from Buttplug server...")
        if self.client.is_connected:
            # Create the async disconnect task
            async def do_disconnect():
                await self.stop() # Ensure device is stopped first
                await self.client.disconnect()
            
            future = asyncio.run_coroutine_threadsafe(do_disconnect(), self.loop)
            try:
                future.result(timeout=3.0)
                print("✅ Client disconnected.")
            except Exception as e:
                print(f"🔥 Error during disconnect: {e}")
        
        # Finally, stop the event loop thread
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)