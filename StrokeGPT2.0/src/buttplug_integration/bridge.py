"""ButtplugBridge skeleton to manage device lifecycle and translation to StrokeGPT commands."""

from __future__ import annotations

from typing import Optional, Dict, Any

from .translator import ButtplugTranslator, StrokeGPTCommand
from .devices import DeviceSpec

class ButtplugBridge:
    """
    Lightweight bridge that coordinates between the Buttplug translator and a device
    interface. This skeleton provides the minimal surface needed for integration work.
    """

    def __init__(self, translator: Optional[ButtplugTranslator] = None) -> None:
        self.translator = translator or ButtplugTranslator()
        self.device: DeviceSpec | None = None
        self.connected: bool = False

    def connect_device(self, device_spec: DeviceSpec) -> bool:
        """
        Establish a logical connection to a device.
        In a full implementation, this would open a session with a Buttplug server.
        Here we simply store the spec and mark connected for the skeleton.
        """
        self.device = device_spec
        self.connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect the current device and reset internal state."""
        self.device = None
        self.connected = False

    def handle_buttplug_message(self, message: Dict[str, Any]) -> StrokeGPTCommand:
        """
        Translate a received Buttplug message to a StrokeGPT command using the translator.
        """
        return self.translator.translate(message)

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "device": self.device.name if self.device else None,
        }