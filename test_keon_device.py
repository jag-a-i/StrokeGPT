#!/usr/bin/env python3
"""
Simple test script for Keon device connection and movement
"""
import time
from buttplug_controller import ButtplugController

def test_keon_device():
    """Test Keon device connection and basic movement"""
    print("Keon Device Test Script")
    print("=" * 50)
    
    # Initialize controller
    print("Initializing ButtplugController...")
    controller = ButtplugController()
    
    try:
        # Test connection
        print("\nConnecting to Intiface Central...")
        controller.connect()
        
        # Wait for connection and device discovery
        print("Scanning for devices (this may take a few seconds)...")
        time.sleep(5)  # Give some time for device discovery
        
        if not controller.is_connected:
            print("\nFailed to connect to Intiface Central or no devices found.")
            print("Please ensure:")
            print("  1. Intiface Central is installed and running")
            print("  2. Your Keon device is connected and paired with your computer")
            print("  3. Intiface Central has discovered your device")
            return
            
        print(f"\nSuccessfully connected to device: {controller.device.name}")
        print(f"   Vibrator actuators: {len(controller._vibrator_actuators)}")
        print(f"   Linear actuators: {len(controller._linear_actuators)}")
        print(f"   Rotatory actuators: {len(controller._rotatory_actuators)}")
        
        # Test basic movement if device has linear actuators
        if controller._linear_actuators:
            print("\nTesting linear movement...")
            print("Moving to position 50% with speed 50%...")
            controller.move(speed=50, depth=50, stroke_range=50)
            time.sleep(3)
            
            print("\nStopping device...")
            controller.stop()
            time.sleep(1)
            
            # Test different speeds
            print("\nTesting different speeds...")
            controller.move(speed=30, depth=50, stroke_range=30)
            time.sleep(2)
            controller.stop()
            time.sleep(1)
            
            controller.move(speed=70, depth=50, stroke_range=70)
            time.sleep(2)
            controller.stop()
            
        # Test vibration if device has vibrator actuators
        if controller._vibrator_actuators:
            print("\nTesting vibration...")
            controller.move(speed=30, depth=0, stroke_range=0)  # Just vibration
            time.sleep(2)
            controller.stop()
            time.sleep(1)
            
            controller.move(speed=70, depth=0, stroke_range=0)  # Higher intensity
            time.sleep(2)
            controller.stop()
        
        print("\nAll tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up...")
        controller.disconnect()
        print("Done!")

if __name__ == "__main__":
    test_keon_device()