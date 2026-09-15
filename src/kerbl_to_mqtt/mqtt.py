from __future__ import annotations

import json
from typing import Any

import paho.mqtt.client as mqtt


class MqttPublisher:
    def __init__(self, host: str, port: int, username: str | None, password: str | None, tls: bool, prefix: str) -> None:
        self.prefix = prefix
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="kerbl-to-mqtt")
        if username:
            self.client.username_pw_set(username, password)
        if tls:
            self.client.tls_set()
        self.client.will_set(f"{prefix}/status", "offline", qos=1, retain=True)
        self.client.connect(host, port, keepalive=60)
        self.client.loop_start()
        self.publish("status", "online", retain=True)

    def publish(self, topic: str, payload: Any, retain: bool = True) -> None:
        body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        result = self.client.publish(f"{self.prefix}/{topic.lstrip('/')}", body, qos=1, retain=retain)
        result.wait_for_publish()
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with code {result.rc}")

    def publish_device(self, device_type: str, device_id: str, state: dict[str, Any], observed_at: str) -> None:
        topic = f"devices/{device_type}/{device_id}"
        self.publish(f"{topic}/observed_at", observed_at)
        self._publish_tree(topic, state)
        self.publish(f"{topic}/availability", "online")

    def _publish_tree(self, topic: str, value: Any) -> None:
        if isinstance(value, dict):
            if not value:
                return
            for key, child in value.items():
                self._publish_tree(f"{topic}/{_topic_segment(key)}", child)
            return
        if isinstance(value, list):
            if not value:
                return
            for index, child in enumerate(value):
                self._publish_tree(f"{topic}/{index}", child)
            return
        self.publish(topic, value)

    def close(self) -> None:
        self.publish("status", "offline", retain=True)
        self.client.loop_stop()
        self.client.disconnect()


def _topic_segment(value: Any) -> str:
    segment = str(value).strip().replace("/", "_")
    return segment or "_"
