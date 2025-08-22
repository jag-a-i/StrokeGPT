"""Buttplug integration translator skeleton for StrokeGPT 2.0."""
from __future__ import annotations

from typing import Any, Dict, Optional

class StrokeGPTCommand:
    """
    Lightweight representation of a StrokeGPT command produced by the translation layer.
    This acts as a simple data container; the real runtime would convert this into
    concrete API calls to the StrokeGPT actuator interface.
    """
    def __init__(self, action: str, params: Optional[Dict[str, Any]] = None) -> None:
        self.action = action
        self.params = params or {}

    def __repr__(self) -> str:
        return f"StrokeGPTCommand(action={self.action!r}, params={self.params!r})"

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "params": self.params}

class ButtplugTranslator:
    """
    Translator that converts Buttplug protocol messages to StrokeGPT commands.
    This is a minimal skeleton intended to support early integration work.
    """
    def __init__(self, mapping: Optional[Dict[str, Any]] = None) -> None:
        # Allow injection of explicit mappings in future iterations
        self.mapping = mapping or {}

    def translate(self, message: Dict[str, Any]) -> StrokeGPTCommand:
        """
        Translate a Buttplug message into a StrokeGPTCommand.

        Expected input shape (minimal):
        {
          "type": "<string>",  # e.g., "Move", "Stop", "Rotate", "Vibrate"
          "payload": { ... }   # optional
        }

        Returns a StrokeGPTCommand instance.
        """
        if not isinstance(message, dict):
            raise TypeError("message must be a dict")

        msg_type = message.get("type")
        payload = message.get("payload", {})

        if not msg_type:
            # Fallback to a generic "unknown" command
            return StrokeGPTCommand("unknown", {"raw": message})

        t = str(msg_type).lower()
        if t == "move":
            direction = payload.get("direction", "unknown")
            speed = payload.get("speed", 0)
            return StrokeGPTCommand("move", {"direction": direction, "speed": speed})

        if t == "stop":
            return StrokeGPTCommand("stop", {})

        if t == "rotate":
            axis = payload.get("axis", "yaw")
            angle = payload.get("angle", 0)
            return StrokeGPTCommand("rotate", {"axis": axis, "angle": angle})

        if t == "vibrate":
            intensity = payload.get("intensity", 0)
            duration = payload.get("duration", 0)
            return StrokeGPTCommand("vibrate", {"intensity": intensity, "duration": duration})

        # Fallback for unknown message types
        return StrokeGPTCommand("unknown", {"message": message})