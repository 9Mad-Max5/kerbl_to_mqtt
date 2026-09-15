# Kerbl to MQTT

Kleiner, read-only Python-Dienst als Bruecke zwischen der inoffiziellen Kerbl-IoT-API und MQTT. Er meldet sich bei Kerbl an, liest konfigurierte Geraete in einem festen Intervall und veroeffentlicht deren vollstaendigen Zustand als JSON.

## Docker Compose

Voraussetzung ist eine installierte Docker-Desktop-Version mit Compose-Unterstützung.

Der Compose-Stack besteht aus zwei Containern:

- `kerbl-to-mqtt`: der Python-Bridge-Dienst
- `mqtt`: ein lokaler Eclipse-Mosquitto-Broker

### Lokales Image bauen

Die normale Datei [docker-compose.yml](docker-compose.yml) baut das Python-Image aus dem aktuellen Quellcode:

1. `.env.example` nach `.env` kopieren.
2. In `.env` Kerbl-Zugangsdaten, Gerätenamen und MQTT-Einstellungen konfigurieren.
3. Images bauen und Stack im Hintergrund starten:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

### Vorhandenes Image verwenden

Wenn das Bridge-Image bereits lokal vorhanden oder in einer Registry veröffentlicht ist, kann die build-freie Datei [docker-compose.image.yml](docker-compose.image.yml) verwendet werden:

```powershell
$env:KERBL_TO_MQTT_IMAGE = "ghcr.io/dein-benutzername/kerbl-to-mqtt:latest"
docker compose -f docker-compose.image.yml up -d
```

Ohne `KERBL_TO_MQTT_IMAGE` wird das lokale Image `kerbl-to-mqtt:latest` erwartet. Dieses kann beispielsweise vorher mit `docker build -t kerbl-to-mqtt:latest .` gebaut werden. Die build-freie Compose-Datei baut selbst nichts und kann daher erst starten, wenn dieses Image verfügbar ist.

Der Status kann so geprüft werden:

```powershell
docker compose ps
docker compose logs -f kerbl-to-mqtt
```

MQTT ist lokal unter `localhost:1883` erreichbar. Zum Beenden:

```powershell
docker compose down
```

Das Standardintervall ist 900 Sekunden (15 Minuten). Der lokale Broker ist absichtlich ohne Authentifizierung konfiguriert. Für einen produktiven MQTT-Broker müssen `MQTT_HOST`, `MQTT_PORT`, Zugangsdaten und gegebenenfalls `MQTT_TLS=true` in `.env` gesetzt werden. Der Dienst veröffentlicht unter `kerbl/...` und nimmt keine MQTT-Schreibbefehle an.

## Lokale Konfiguration mit `.env`

Unter Windows kann lokal einfach `.env.example` nach `.env` kopiert und angepasst werden. Der Python-Start lädt diese Datei automatisch; Docker Compose verwendet sie ebenfalls über `env_file`.

```powershell
Copy-Item .env.example .env
# .env bearbeiten
$env:PYTHONPATH = "src"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m kerbl_to_mqtt
```

Die Datei `.env` ist in `.gitignore` eingetragen und wird nicht committet. Docker Compose und der lokale Python-Start verwenden dieselben Variablennamen.
Der laufende Prozess kann im selben Terminal mit `Ctrl+C` sofort beendet werden. In Docker beendet `docker compose down` den Dienst über `SIGTERM`.

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

### Integration in eine bestehende Compose-Datei

Wenn du Kerbl zusammen mit anderen Diensten wie Sonarr betreibst, kannst du diesen Service in deine bestehende Compose-Datei aufnehmen:

```yaml
  kerbl-to-mqtt:
    image: ghcr.io/DEIN-GITHUB-USERNAME/kerbl-to-mqtt:latest
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
    restart: unless-stopped
```

Die Werte werden hier direkt im Container unter `environment` gesetzt. Ersetze insbesondere `KERBL_EMAIL`, `KERBL_PASSWORD`, den Gerätenamen und das Image. Diese Variante sollte nur in einer nicht öffentlichen Compose-Datei verwendet werden, weil das Passwort sonst im Klartext in der Datei steht. Für ein öffentliches Repository bleiben `.env`, Docker Secrets oder ein Secret-Manager die bessere Lösung.

### Umgebungsvariablen

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

Wenn bereits ein MQTT-Broker vorhanden ist, kann der `mqtt`-Service entfallen. Der Kerbl-Service muss dann nur mit dem Docker-Netzwerk des bestehenden Brokers verbunden werden. `privileged` und veröffentlichte Ports sind für `kerbl-to-mqtt` nicht erforderlich.
## Lokal testen

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest
```

Die API stammt aus [9Mad-Max5/kerbl_api](https://github.com/9Mad-Max5/kerbl_api). Sie ist inoffiziell und kann sich ohne Vorankuendigung aendern.
