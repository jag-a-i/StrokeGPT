import asyncio
import threading
from buttplug import Client, WebsocketConnector, ButtplugClientDevice

# Using hardcoded buttplug server url, could be made more flexible
class ButtplugController:
    def __init__(self, server_uri="ws://127.0.0.1:12345"):
        self.server_uri = server_uri
        self.client = Client("StrokeGPT Client")
        self.device = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect(self):
        try:
            connector = WebsocketConnector(self.server_uri)
            await self.client.connect(connector)
            print("? Connected to Buttplug server.")
            await self.scan_for_devices()
        except Exception as e:
            print(f"?? Could not connect to Buttplug server: {e}")

    async def _scan_for_devices(self):
        await self.client.start_scanning()
        await asyncio.sleep(5) # Scan for 5 seconds
        await self.client.stop_scanning()
        
        if not self.client.devices:
            print("?? No devices found.")
            return

        # Try to find a linear-capable device first
        for dev in self.client.devices.values():
            if "Linear" in dev.allowed_messages:
                self.device = dev
                print(f"? Found linear device: {self.device.name}")
                return
        
        # Fallback to first vibrator
        for dev in self.client.devices.values():
            if "Vibrate" in dev.allowed_messages:
                self.device = dev
                print(f"?? No linear device. Found vibrating device: {self.device.name}")
                return

    def connect(self):
        # Run the async connect function in the event loop thread
        asyncio.run_coroutine_threadsafe(self._connect(), self.loop)

    def _translate_and_send(self, speed, depth, stroke_range):
        if not self.device:
            print("?? Buttplug move called but no device connected.")
            return

        # --- THIS IS THE TRICKY PART ---
        # You must translate StrokeGPT's concept of speed/depth/range
        # into Buttplug's concept of position/duration.

        # Example for a stroker (Linear):
        if "Linear" in self.device.allowed_messages:
            # 1. Calculate target position from 'depth' and 'stroke_range'
            # Buttplug position is 0.0 (in) to 1.0 (out).
            center_pos = depth / 100.0
            half_range = (stroke_range / 100.0) / 2.0
            pos1 = max(0.0, center_pos - half_range)
            pos2 = min(1.0, center_pos + half_range)

            # 2. Calculate duration from 'speed'
            # Higher speed = lower duration.
            # This requires experimentation. A value of 2000ms might be a good start.
            duration_ms = int(2000 * (1 - (speed / 100.0)))
            
            # Send two commands to move back and forth
            # This is a simplified example; a real implementation would need a loop
            # TODO: Create loop
	    async def stroke_pattern():
                await self.device.linear(duration_ms, pos1)
                await asyncio.sleep(duration_ms / 1000)
                await self.device.linear(duration_ms, pos2)

            asyncio.run_coroutine_threadsafe(stroke_pattern(), self.loop)

        # Example for a vibrator:
        elif "Vibrate" in self.device.allowed_messages:
            vibration_speed = speed / 100.0
            asyncio.run_coroutine_threadsafe(self.device.vibrate(vibration_speed), self.loop)

    def move(self, speed, depth, stroke_range):
        if speed is not None and speed == 0:
            self.stop()
            return
        self._translate_and_send(speed, depth, stroke_range)

    def stop(self):
        if self.device:
            asyncio.run_coroutine_threadsafe(self.device.stop(), self.loop)
            print("?? Sent stop command via Buttplug.")
            
    def disconnect(self):
        if self.client.is_connected:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
        self.loop.call_soon_threadsafe(self.loop.stop)
