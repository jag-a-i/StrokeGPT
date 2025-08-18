#!/usr/bin/env python3
"""
Test script for Buttplug device movement
This script tests the basic functionality of the ButtplugController with a real device.
"""

import asyncio
import time
from buttplug_controller import ButtplugController

async def test_device_movement():
    """Test device movement functionality"""
    print("Starting Buttplug device movement test...")
    
    # Initialize controller
    controller = ButtplugController("ws://127.0.0.1:12345")
    
    try:
        # Connect to device
        print("Connecting to Buttplug server...")
        controller.connect()
        
        # Wait a moment for connection
        await asyncio.sleep(2)
        
        if not controller.is_connected:
            print("Failed to connect to device")
            return
            
        print("Successfully connected to device")
        print(f"   Device: {controller.device.name if controller.device else 'Unknown'}")
        print(f"   Vibrator actuators: {len(controller._vibrator_actuators)}")
        print(f"   Linear actuators: {len(controller._linear_actuators)}")
        print(f"   Rotatory actuators: {len(controller._rotatory_actuators)}")
        
        # Test different movement patterns
        print("\nTesting movement patterns...")
        
        # Test 1: Simple vibration
        print("   Testing vibration...")
        controller.move(speed=30, depth=50, stroke_range=0)
        await asyncio.sleep(3)
        controller.stop()
        await asyncio.sleep(1)
        
        # Test 2: Medium vibration
        print("   Testing medium vibration...")
        controller.move(speed=60, depth=50, stroke_range=0)
        await asyncio.sleep(3)
        controller.stop()
        await asyncio.sleep(1)
        
        # Test 3: Linear movement (if available)
        if controller._linear_actuators:
            print("   Testing linear movement...")
            controller.move(speed=50, depth=50, stroke_range=50)
            await asyncio.sleep(5)
            controller.stop()
            await asyncio.sleep(1)
            
            # Test 4: Deep stroke
            print("   Testing deep stroke...")
            controller.move(speed=70, depth=80, stroke_range=70)
            await asyncio.sleep(5)
            controller.stop()
            await asyncio.sleep(1)
        
        # Test 5: Teasing pattern
        print("   Testing teasing pattern...")
        controller.move(speed=20, depth=10, stroke_range=20)
        await asyncio.sleep(3)
        controller.stop()
        
        print("\nAll movement tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ensure device is stopped and disconnected
        print("\nStopping device...")
        controller.stop()
        await asyncio.sleep(1)
        
        print("Disconnecting...")
        controller.disconnect()
        await asyncio.sleep(1)
        
        print("Test completed")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_device_movement())