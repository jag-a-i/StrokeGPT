#!/usr/bin/env python3
"""
Interactive test script for Buttplug device control
This script allows manual control of a Buttplug device for testing purposes.
"""

import asyncio
import sys
from buttplug_controller import ButtplugController

class InteractiveTester:
    def __init__(self):
        self.controller = ButtplugController("ws://127.0.0.1:12345")
        self.connected = False
        
    async def connect(self):
        """Connect to the device"""
        print("🔌 Connecting to Buttplug server...")
        self.controller.connect()
        
        # Wait for connection
        await asyncio.sleep(2)
        
        if self.controller.is_connected:
            self.connected = True
            print("✅ Successfully connected!")
            print(f"   Device: {self.controller.device.name if self.controller.device else 'Unknown'}")
            print(f"   Vibrator actuators: {len(self.controller._vibrator_actuators)}")
            print(f"   Linear actuators: {len(self.controller._linear_actuators)}")
            print(f"   Rotatory actuators: {len(self.controller._rotatory_actuators)}")
            return True
        else:
            print("❌ Failed to connect to device")
            return False
    
    def show_help(self):
        """Show available commands"""
        print("\n🔧 Available Commands:")
        print("  connect     - Connect to device")
        print("  disconnect  - Disconnect from device")
        print("  vibrate <intensity> - Set vibration intensity (0-100)")
        print("  move <speed> <depth> <range> - Move with specified parameters")
        print("  stop        - Stop all movement")
        print("  status      - Show connection status")
        print("  actuators   - List available actuators")
        print("  help        - Show this help")
        print("  quit        - Exit the program")
        print()
    
    def show_status(self):
        """Show current status"""
        if self.connected and self.controller.is_connected:
            print("✅ Connected to device")
            print(f"   Device: {self.controller.device.name}")
            print(f"   Last speed: {self.controller.last_relative_speed}")
            print(f"   Last depth: {self.controller.last_depth_pos}")
        else:
            print("❌ Not connected to device")
    
    def list_actuators(self):
        """List available actuators"""
        if not self.connected or not self.controller.is_connected:
            print("❌ Not connected to device")
            return
            
        print("🔍 Available Actuators:")
        for i, actuator in enumerate(self.controller._vibrator_actuators):
            print(f"   Vibrator {i}: {actuator.description}")
        for i, actuator in enumerate(self.controller._linear_actuators):
            print(f"   Linear {i}: {actuator.description}")
        for i, actuator in enumerate(self.controller._rotatory_actuators):
            print(f"   Rotatory {i}: {actuator.description}")
    
    async def vibrate(self, intensity):
        """Set vibration intensity"""
        if not self.connected or not self.controller.is_connected:
            print("❌ Not connected to device")
            return
            
        try:
            intensity = float(intensity)
            if 0 <= intensity <= 100:
                # For testing, we'll use the move method which handles actuators properly
                self.controller.move(intensity, 50, 0)  # depth=50, range=0 for vibration only
                print(f"✅ Vibration set to {intensity}%")
            else:
                print("❌ Intensity must be between 0 and 100")
        except ValueError:
            print("❌ Invalid intensity value")
    
    async def move_device(self, speed, depth, stroke_range):
        """Move device with specified parameters"""
        if not self.connected or not self.controller.is_connected:
            print("❌ Not connected to device")
            return
            
        try:
            speed = float(speed)
            depth = float(depth)
            stroke_range = float(stroke_range)
            
            if not (0 <= speed <= 100):
                print("❌ Speed must be between 0 and 100")
                return
            if not (0 <= depth <= 100):
                print("❌ Depth must be between 0 and 100")
                return
            if not (0 <= stroke_range <= 100):
                print("❌ Stroke range must be between 0 and 100")
                return
                
            self.controller.move(speed, depth, stroke_range)
            print(f"✅ Moving device - Speed: {speed}%, Depth: {depth}%, Range: {stroke_range}%")
        except ValueError:
            print("❌ Invalid parameter values")
    
    async def stop_device(self):
        """Stop device movement"""
        if not self.connected or not self.controller.is_connected:
            print("❌ Not connected to device")
            return
            
        self.controller.stop()
        print("🛑 Device stopped")
    
    async def disconnect(self):
        """Disconnect from device"""
        if self.connected:
            print("🔌 Disconnecting...")
            self.controller.disconnect()
            self.connected = False
            await asyncio.sleep(1)
            print("✅ Disconnected")
        else:
            print("❌ Not connected")
    
    async def run(self):
        """Run the interactive tester"""
        print("🎮 Interactive Buttplug Device Tester")
        print("Type 'help' for available commands")
        print()
        
        self.show_help()
        
        while True:
            try:
                command = input("\n> ").strip().split()
                if not command:
                    continue
                    
                cmd = command[0].lower()
                
                if cmd == "quit" or cmd == "exit":
                    break
                elif cmd == "help":
                    self.show_help()
                elif cmd == "connect":
                    if not self.connected:
                        await self.connect()
                    else:
                        print("✅ Already connected")
                elif cmd == "disconnect":
                    await self.disconnect()
                elif cmd == "vibrate":
                    if len(command) > 1:
                        await self.vibrate(command[1])
                    else:
                        print("❌ Usage: vibrate <intensity>")
                elif cmd == "move":
                    if len(command) > 3:
                        await self.move_device(command[1], command[2], command[3])
                    else:
                        print("❌ Usage: move <speed> <depth> <range>")
                elif cmd == "stop":
                    await self.stop_device()
                elif cmd == "status":
                    self.show_status()
                elif cmd == "actuators":
                    self.list_actuators()
                else:
                    print(f"❌ Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Clean up
        if self.connected:
            await self.disconnect()
        
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    tester = InteractiveTester()
    asyncio.run(tester.run())