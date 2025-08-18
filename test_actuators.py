#!/usr/bin/env python3
"""
Comprehensive test script for Buttplug device actuators
This script tests the specific actuator functionality of the ButtplugController.
"""

import asyncio
import time
from buttplug_controller import ButtplugController

async def test_actuator_functionality():
    """Test individual actuator functionality"""
    print("Starting Buttplug actuator functionality test...")
    
    # Initialize controller
    controller = ButtplugController("ws://127.0.0.1:12345")
    
    try:
        # Connect to device
        print("Connecting to Buttplug server...")
        controller.connect()
        
        # Wait a moment for connection
        await asyncio.sleep(2)
        
        # Check if connected
        if not controller.is_connected:
            print("Failed to connect to device")
            return
            
        print("Successfully connected to device")
        print(f"   Device: {controller.device.name if controller.device else 'Unknown'}")
        print(f"   Vibrator actuators: {len(controller._vibrator_actuators)}")
        print(f"   Linear actuators: {len(controller._linear_actuators)}")
        print(f"   Rotatory actuators: {len(controller._rotatory_actuators)}")
        
        # Test individual actuators
        if controller._vibrator_actuators:
            print("\nTesting vibrator actuators...")
            for i, actuator in enumerate(controller._vibrator_actuators):
                print(f"   Testing vibrator actuator {i}: {actuator.description}")
                try:
                    await actuator.command(0.3)  # 30% intensity
                    await asyncio.sleep(2)
                    await actuator.command(0.0)  # Stop
                    print(f"   Vibrator actuator {i} working")
                except Exception as e:
                    print(f"   Vibrator actuator {i} failed: {e}")
                await asyncio.sleep(1)
        
        if controller._linear_actuators:
            print("\nTesting linear actuators...")
            for i, actuator in enumerate(controller._linear_actuators):
                print(f"   Testing linear actuator {i}: {actuator.description}")
                try:
                    await actuator.command(500, 0.3)  # 500ms, 30% position
                    await asyncio.sleep(1)
                    await actuator.command(500, 0.7)  # 500ms, 70% position
                    await asyncio.sleep(1)
                    await actuator.command(100, 0.5)  # 100ms, 50% position (back to center)
                    print(f"   Linear actuator {i} working")
                except Exception as e:
                    print(f"   Linear actuator {i} failed: {e}")
                await asyncio.sleep(1)
        
        if controller._rotatory_actuators:
            print("\nTesting rotatory actuators...")
            for i, actuator in enumerate(controller._rotatory_actuators):
                print(f"   Testing rotatory actuator {i}: {actuator.description}")
                try:
                    await actuator.command(0.5, True)  # 50% speed, clockwise
                    await asyncio.sleep(2)
                    await actuator.command(0.0, True)  # Stop
                    print(f"   Rotatory actuator {i} working")
                except Exception as e:
                    print(f"   Rotatory actuator {i} failed: {e}")
                await asyncio.sleep(1)
        
        print("\nAll actuator tests completed!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ensure device is stopped and disconnected
        print("\n🛑 Stopping all actuators...")
        try:
            # Stop all actuators
            for actuator in controller._vibrator_actuators:
                await actuator.command(0.0)
            for actuator in controller._linear_actuators:
                await actuator.command(100, 0.5)
            for actuator in controller._rotatory_actuators:
                await actuator.command(0.0, True)
        except:
            pass
            
        await asyncio.sleep(1)
        
        print("Disconnecting...")
        controller.disconnect()
        await asyncio.sleep(1)
        
        print("Actuator test completed")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_actuator_functionality())