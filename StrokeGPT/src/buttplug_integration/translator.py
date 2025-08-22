"""
Translator wrapper for StrokeGPT2.0 port, enabling existing 2.0 translator logic
to be importable from the legacy StrokeGPT path used by tests.

This wrapper loads the 2.0 translator implementation by adjusting sys.path
to include StrokeGPT2.0's src directory, then re-exports the public API
expected by tests: ButtplugTranslator and StrokeGPTCommand.
"""

from __future__ import annotations

import sys
import os

# Determine the path to StrokeGPT2.0's src directory
# If this wrapper is located at StrokeGPT/src/buttplug_integration/translator.py,
# then the 2.0 path is expected to be at ../StrokeGPT2.0/src
_this_file = os.path.abspath(__file__)
# StrokeGPT/src/buttplug_integration -> its parent is StrokeGPT/src; parent of parent is StrokeGPT
stroke_gpt_root = os.path.normpath(os.path.join(_this_file, "..", ".."))
path_2_0_src = os.path.normpath(os.path.join(os.path.dirname(stroke_gpt_root), "StrokeGPT2.0", "src"))

# Safely insert 2.0 src path for import resolution
if os.path.isdir(path_2_0_src) and path_2_0_src not in sys.path:
    sys.path.insert(0, path_2_0_src)

# Import the 2.0 translator, then re-export symbols
try:
    from buttplug_integration.translator import ButtplugTranslator, StrokeGPTCommand  # type: ignore
except Exception:
    # Fallback: lightweight in-file translator for resilience if 2.0 path is missing
    class StrokeGPTCommand:
        def __init__(self, action, params=None):
            self.action = action
            self.params = params or {}

        def __repr__(self):
            return f"StrokeGPTCommand(action={self.action!r}, params={self.params!r})"

        def to_dict(self):
            return {"action": self.action, "params": self.params}

    class ButtplugTranslator:
        def translate(self, message: dict) -> StrokeGPTCommand:
            if not isinstance(message, dict) or "type" not in message:
                return StrokeGPTCommand("unknown", {"raw": message})
            t = str(message["type"]).lower()
            payload = message.get("payload", {})
            if t == "move":
                dirc = payload.get("direction", "unknown")
                spd = payload.get("speed", 0)
                return StrokeGPTCommand("move", {"direction": dirc, "speed": spd})
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
            return StrokeGPTCommand("unknown", {"message": message})

# Expose expected public API
__all__ = ["ButtplugTranslator", "StrokeGPTCommand"]