"""Tests for Buttplug integration translator and bridge skeleton for StrokeGPT 2.0."""

from buttplug_integration.translator import ButtplugTranslator, StrokeGPTCommand
from buttplug_integration.bridge import ButtplugBridge
from buttplug_integration.devices import DeviceSpec


def test_translator_move():
    t = ButtplugTranslator()
    cmd = t.translate({"type": "Move", "payload": {"direction": "forward", "speed": 7}})
    assert isinstance(cmd, StrokeGPTCommand)
    assert cmd.action == "move"
    assert cmd.params["direction"] == "forward"
    assert cmd.params["speed"] == 7


def test_translator_stop():
    t = ButtplugTranslator()
    cmd = t.translate({"type": "Stop"})
    assert isinstance(cmd, StrokeGPTCommand)
    assert cmd.action == "stop"


def test_translator_rotate():
    t = ButtplugTranslator()
    cmd = t.translate({"type": "Rotate", "payload": {"axis": "yaw", "angle": 45}})
    assert cmd.action == "rotate"
    assert cmd.params["axis"] == "yaw"
    assert cmd.params["angle"] == 45


def test_translator_unknown():
    t = ButtplugTranslator()
    cmd = t.translate({"type": "FooBar"})
    assert isinstance(cmd, StrokeGPTCommand)
    assert cmd.action == "unknown"


def test_bridge_connect_and_translate():
    t = ButtplugTranslator()
    bridge = ButtplugBridge(translator=t)
    device = DeviceSpec(id="dev1", name="TestDevice", address="", port=0, capabilities=[])
    bridge.connect_device(device)
    status = bridge.get_status()
    assert status["connected"] is True
    assert status["device"] == "TestDevice"

    cmd = bridge.handle_buttplug_message({"type": "Move", "payload": {"direction": "left", "speed": 3}})
    assert isinstance(cmd, StrokeGPTCommand)