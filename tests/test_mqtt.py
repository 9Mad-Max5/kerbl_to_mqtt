from kerbl_to_mqtt.mqtt import MqttPublisher


def test_publish_device_splits_nested_values_into_topics():
    publisher = MqttPublisher.__new__(MqttPublisher)
    publisher.prefix = "kerbl"
    calls = []
    publisher.publish = lambda topic, payload, retain=True: calls.append((topic, payload, retain))

    publisher.publish_device(
        "smart-coop",
        "coop-1",
        {
            "isOnline": True,
            "Voltage": 12,
            "sensors": {"temperature": 21.5},
            "events": [{"level": "warning"}],
        },
        "2026-09-15T12:00:00+00:00",
    )

    topics = {topic: payload for topic, payload, _retain in calls}
    assert "devices/smart-coop/coop-1" not in topics
    assert topics["devices/smart-coop/coop-1/isOnline"] is True
    assert topics["devices/smart-coop/coop-1/Voltage"] == 12
    assert topics["devices/smart-coop/coop-1/sensors/temperature"] == 21.5
    assert "devices/smart-coop/coop-1/sensors/temperature/unit" not in topics
    assert topics["devices/smart-coop/coop-1/events/0/level"] == "warning"
    assert topics["devices/smart-coop/coop-1/observed_at"] == "2026-09-15T12:00:00+00:00"


def test_publish_nested_value_does_not_use_parent_field_for_unit():
    publisher = MqttPublisher.__new__(MqttPublisher)
    publisher.prefix = "kerbl"
    calls = []
    publisher.publish = lambda topic, payload, retain=True: calls.append((topic, payload))

    publisher.publish_device("smart-coop", "coop-1", {"Voltage": {"value": 12}}, "now")

    topics = dict(calls)
    assert topics["devices/smart-coop/coop-1/Voltage/value"] == 12
    assert "devices/smart-coop/coop-1/Voltage/value/unit" not in topics