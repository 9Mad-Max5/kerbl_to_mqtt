# Kerbl to MQTT

Kleiner, read-only Python-Dienst als Bruecke zwischen der inoffiziellen Kerbl-IoT-API und MQTT. Er meldet sich bei Kerbl an, liest konfigurierte Geraete in einem festen Intervall und veroeffentlicht deren vollstaendigen Zustand als JSON.

## Docker Compose

Das veröffentlichte Image liegt unter:

```text
ghcr.io/9mad-max5/kerbl_to_mqtt:latest
```

Image beziehen:

```powershell
docker pull ghcr.io/9mad-max5/kerbl_to_mqtt:latest
```

Falls das GHCR-Paket privat ist, vorher mit einem GitHub-Token und `read:packages` anmelden:

```powershell
docker login ghcr.io -u 9Mad-Max5
```

Für deine bestehende Compose-Datei kannst du den Dienst direkt ergänzen:

```yaml
  kerbl-to-mqtt:
    image: ghcr.io/9mad-max5/kerbl_to_mqtt:latest
    container_name: kerbl-to-mqtt
    environment:
      KERBL_EMAIL: "deine-mail@example.com"
      KERBL_PASSWORD: "dein-passwort"
      KERBL_BASE_URL: "https://backend.kerbl-iot.com"
      KERBL_DEVICES: '[{"type":"smart-coop","name":"Hühnerstall"}]'
      MQTT_HOST: "mqtt"
      MQTT_PORT: "1883"
      MQTT_USERNAME: ""
      MQTT_PASSWORD: ""
      MQTT_TLS: "false"
      MQTT_TOPIC_PREFIX: "kerbl"
      POLL_INTERVAL_SECONDS: "900"
      TZ: "${TZ}"
    networks:
      - mqtt
    restart: unless-stopped
```

Der MQTT-Broker muss im selben Docker-Netzwerk unter dem Namen `mqtt` erreichbar sein. Der Dienst benötigt weder `privileged` noch einen veröffentlichten Port.

```powershell
docker compose up -d
docker compose logs -f kerbl-to-mqtt
docker compose down
```

Das Standard-Polling-Intervall beträgt 15 Minuten. GitHub Actions veröffentlicht das Image nach Pushes auf den Standard-Branch in GHCR.

## Geraete konfigurieren

`KERBL_DEVICES` ist ein JSON-Array. Geräte können über ihren exakten Anzeigenamen ausgewählt werden:

```dotenv
KERBL_DEVICES=[{"type":"smart-coop","name":"Hühnerstall"}]
```

Der Name wird gegen `description` beziehungsweise `name` aus der Kerbl-Geräteliste verglichen. Bei mehreren Geräten mit demselben Namen muss ein eindeutiger Name verwendet werden. IDs werden weiterhin unterstützt:

```dotenv
KERBL_DEVICES=[{"type":"smart-coop","id":"abc123"}]
```

Unterstuetzte Typen werden vom Adapter auf die Kerbl-Pfade abgebildet, unter anderem `smart-coop`, `smart-energizer`, `smart-satellite`, `smart-weather`, `smart-tracker` und `smart-chickendoor`.

## MQTT-Topics

- `kerbl/status`: `online` oder `offline`, retained mit Last Will
- `kerbl/devices/<type>/<id>/<feld>`: jedes einfache Feld einzeln als retained JSON-Wert
- Verschachtelte Objekte werden weiter aufgeteilt, zum Beispiel `.../sensors/temperature`
- Listen werden über numerische Untertopics veröffentlicht, zum Beispiel `.../events/0`
- `kerbl/devices/<type>/<id>/availability`: `online` nach erfolgreichem Lesen

Der Dienst verwendet nur HTTP-GET fuer Geraetedaten. Es gibt keine MQTT-Kommandos und keine Aufrufe der Kerbl-Schreibmethoden.

## Variablen

Diese Variablen werden vom `kerbl-to-mqtt`-Container verwendet:

| Variable | Pflicht | Beschreibung | Standard |
| --- | --- | --- | --- |
| `KERBL_EMAIL` | Ja | E-Mail-Adresse des Kerbl-IoT-Kontos | - |
| `KERBL_PASSWORD` | Ja | Passwort des Kerbl-IoT-Kontos | - |
| `KERBL_BASE_URL` | Nein | Kerbl-Backend, normalerweise Produktion | `https://backend.kerbl-iot.com` |
| `KERBL_DEVICES` | Ja | JSON-Array der Geräte, Auswahl per `name` oder `id` | - |
| `MQTT_HOST` | Nein | DNS-Name oder IP-Adresse des MQTT-Brokers | `mqtt` |
| `MQTT_PORT` | Nein | MQTT-Port | `1883` |
| `MQTT_USERNAME` | Nein | Benutzername am MQTT-Broker | leer |
| `MQTT_PASSWORD` | Nein | Passwort am MQTT-Broker | leer |
| `MQTT_TLS` | Nein | TLS für MQTT mit `true` aktivieren | `false` |
| `MQTT_TOPIC_PREFIX` | Nein | Präfix für alle veröffentlichten Topics | `kerbl` |
| `POLL_INTERVAL_SECONDS` | Nein | Polling-Intervall in Sekunden, mindestens 10 | `900` |
| `TZ` | Nein | Zeitzone für den Container | Docker-Standard |

`KERBL_DEVICES` verwendet zum Beispiel:

```yaml
KERBL_DEVICES: '[{"type":"smart-coop","name":"Hühnerstall"}]'
```

`KERBL_TO_MQTT_IMAGE` ist keine Anwendungsvariable. Sie wird nur von `docker-compose.image.yml` zur Auswahl des bereits veröffentlichten Container-Images verwendet.

## Lokal testen

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest
```

Die API stammt aus [9Mad-Max5/kerbl_api](https://github.com/9Mad-Max5/kerbl_api). Sie ist inoffiziell und kann sich ohne Vorankuendigung aendern.
