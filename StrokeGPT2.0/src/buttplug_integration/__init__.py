"""Buttplug integration package for StrokeGPT 2.0 (StrokeGPT2.0 port)."""

from .translator import ButtplugTranslator, StrokeGPTCommand
from .bridge import ButtplugBridge
from .devices import DeviceSpec

__all__ = ["ButtplugTranslator", "StrokeGPTCommand", "ButtplugBridge", "DeviceSpec"]

def initialize() -> dict:
    """Initialize the integration runtime (stub)."""
    return {"status": "initialized"}

def connectDevice(device_spec: "DeviceSpec") -> "ButtplugBridge":
    """Create a bridge for a device and connect."""
    bridge = ButtplugBridge(translator=ButtplugTranslator())
    bridge.connect_device(device_spec)
    return bridge

def sendCommand(bridge: "ButtplugBridge", message: dict) -> "StrokeGPTCommand":
    """Translate a Buttplug message via the bridge's translator."""
    return bridge.handle_buttplug_message(message)

def shutdown(bridge: "ButtplugBridge") -> None:
    """Shutdown the bridge connection."""
    bridge.disconnect()