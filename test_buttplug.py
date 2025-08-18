"""
Test script for ButtplugController.
Run this script to test the connection to Intiface Central and device control.
"""
import time
import sys
import os
from buttplug_controller import ButtplugController

# Fix for Windows encoding issue
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

def test_connection():
    print("Initializing ButtplugController...")
    controller = ButtplugController()
    
    try:
        # Test connection
        print("\nConnecting to Intiface Central...")
        controller.connect()
        
        # Wait for connection and device discovery
        print("\nScanning for devices (this may take a few seconds)...")
        time.sleep(5)  # Give some time for device discovery
        
        if not controller.is_connected:
            print("\nFailed to connect to Intiface Central or no devices found.")
            print("Please ensure Intiface Central is running and a device is connected.")
            return
            
        print("\nSuccessfully connected and found a device!")
        
        # Test basic movement
        print("\nTesting basic movement...")
        print("Moving to position 50% with speed 50%...")
        controller.move(speed=50, depth=50, stroke_range=50)
        time.sleep(3)
        
        print("\nStopping device...")
        controller.stop()
        
        # Test vibration (if device supports it)
        # Note: In the new Protocol v3 implementation, we check for actuators instead
        if controller._vibrator_actuators:
            print("\nTesting vibration...")
            controller.move(speed=30, depth=0, stroke_range=0)  # Just vibration, no movement
            time.sleep(2)
            controller.stop()
        
        print("\nAll tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nCleaning up...")
        controller.disconnect()
        print("Done!")

if __name__ == "__main__":
    print("=" * 60)
    print("ButtplugController Test Script")
    print("=" * 60)
    print("\nBefore running this test, please ensure:")
    print("1. Intiface Central is installed and running")
    print("2. Your device is connected and paired with your computer")
    print("3. Intiface Central has discovered your device")
    print("\nPress Enter to start the test...")
    input()
    
    test_connection()