from kerbl_to_mqtt.config import DeviceSelector
from kerbl_to_mqtt.service import Bridge


class FakeKerbl:
    def get_device(self, device_type, device_id):
        return {"id": device_id, "isOnline": True}

    def find_device(self, device_type, name):
        return {"id": "coop-by-name", "description": name, "isOnline": True}


class FakePublisher:
    def __init__(self):
        self.calls = []

    def publish_device(self, device_type, device_id, state, observed_at):
        self.calls.append((device_type, device_id, state, observed_at))


class Settings:
    devices = (DeviceSelector("smart-coop", device_id="coop-1"),)
    poll_interval_seconds = 900


def test_poll_publishes_read_only_device_state():
    publisher = FakePublisher()
    Bridge(Settings(), FakeKerbl(), publisher).poll_once()

    assert len(publisher.calls) == 1
    assert publisher.calls[0][0:3] == ("smart-coop", "coop-1", {"id": "coop-1", "isOnline": True})
    assert publisher.calls[0][3].endswith("+00:00")


def test_poll_resolves_device_by_name():
    settings = type("Settings", (), {
        "devices": (DeviceSelector("smart-coop", name="Hühnerstall"),),
        "poll_interval_seconds": 900,
    })()
    publisher = FakePublisher()
    Bridge(settings, FakeKerbl(), publisher).poll_once()

    assert publisher.calls[0][0:3] == (
        "smart-coop",
        "coop-by-name",
        {"id": "coop-by-name", "description": "Hühnerstall", "isOnline": True},
    )
