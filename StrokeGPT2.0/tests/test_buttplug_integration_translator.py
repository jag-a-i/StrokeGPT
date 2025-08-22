"""Tests for translator behavior in StrokeGPT2.0 port using dynamic import."""

import importlib.util
from pathlib import Path

def _load_translator():
    translator_path = Path(__file__).resolve().parents[2] / "src" / "buttplug_integration" / "translator.py"
    spec = importlib.util.spec_from_file_location("buttplug_integration.translator", translator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module

def test_translator_move():
    mod = _load_translator()
    t = mod.ButtplugTranslator()
    cmd = t.translate({"type": "Move", "payload": {"direction": "forward", "speed": 7}})
    assert isinstance(cmd, mod.StrokeGPTCommand)
    assert cmd.action == "move"
    assert cmd.params["direction"] == "forward"
    assert cmd.params["speed"] == 7

def test_translator_stop():
    mod = _load_translator()
    t = mod.ButtplugTranslator()
    cmd = t.translate({"type": "Stop"})
    assert isinstance(cmd, mod.StrokeGPTCommand)
    assert cmd.action == "stop"

def test_translator_rotate():
    mod = _load_translator()
    t = mod.ButtplugTranslator()
    cmd = t.translate({"type": "Rotate", "payload": {"axis": "yaw", "angle": 45}})
    assert cmd.action == "rotate"
    assert cmd.params["axis"] == "yaw"
    assert cmd.params["angle"] == 45

def test_translator_unknown():
    mod = _load_translator()
    t = mod.ButtplugTranslator()
    cmd = t.translate({"type": "FooBar"})
    assert isinstance(cmd, mod.StrokeGPTCommand)
    assert cmd.action == "unknown"