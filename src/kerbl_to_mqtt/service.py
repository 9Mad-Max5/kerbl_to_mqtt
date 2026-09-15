from __future__ import annotations

import logging
import signal
import time
from datetime import datetime, timezone
from threading import Event

from .config import Settings
from .kerbl import KerblClient
from .mqtt import MqttPublisher

logger = logging.getLogger(__name__)


class Bridge:
    def __init__(self, settings: Settings, kerbl: KerblClient, publisher: MqttPublisher) -> None:
        self.settings = settings
        self.kerbl = kerbl
        self.publisher = publisher
        self.running = True
        self.stop_event = Event()

    def poll_once(self) -> None:
        observed_at = datetime.now(timezone.utc).isoformat()
        for selector in self.settings.devices:
            try:
                device = (
                    self.kerbl.get_device(selector.device_type, selector.device_id)
                    if selector.device_id
                    else self.kerbl.find_device(selector.device_type, selector.name or "")
                )
                device_id = str(device.get("id") or selector.device_id)
                self.publisher.publish_device(selector.device_type, device_id, device, observed_at)
                logger.info("Published %s/%s", selector.device_type, device_id)
            except Exception:
                logger.exception("Polling failed for %s", selector)

    def run(self) -> None:
        while self.running:
            started = time.monotonic()
            self.poll_once()
            remaining = max(0, self.settings.poll_interval_seconds - (time.monotonic() - started))
            logger.info("Next poll in %.0f seconds", remaining)
            if self.running and self.stop_event.wait(remaining):
                break

    def stop(self, *_args: object) -> None:
        self.running = False
        self.stop_event.set()


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_env()
    kerbl = KerblClient(settings.kerbl_email, settings.kerbl_password, settings.kerbl_base_url)
    publisher = MqttPublisher(
        settings.mqtt_host,
        settings.mqtt_port,
        settings.mqtt_username,
        settings.mqtt_password,
        settings.mqtt_tls,
        settings.mqtt_topic_prefix,
    )
    bridge = Bridge(settings, kerbl, publisher)
    signal.signal(signal.SIGTERM, bridge.stop)
    signal.signal(signal.SIGINT, bridge.stop)
    try:
        bridge.run()
    except KeyboardInterrupt:
        bridge.stop()
    finally:
        publisher.close()
