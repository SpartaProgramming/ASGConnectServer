import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import paho.mqtt.client as mqtt
import json
import config
import random
import threading
import time

class MockMQTTHandler:
    def __init__(self, game_state, game_manager=None):
        self.game_state = game_state
        self.game_manager = game_manager
        self.running = False
        self.thread = None
        # Przywrócona lista urządzeń dla mocka
        self.mock_devs = ["ABC111", "DEF222", "GHI333"]

    def start(self):
        print("Uruchomiono MOCK MQTT (Tryb testowy)")
        self.running = True
        self.thread = threading.Thread(target=self._simulate_data, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _simulate_data(self):
        """Generuje sztuczne dane GPS co 2 sekundy"""
        base_lat = 51.10788
        base_lon = 17.03854

        while self.running:
            for dev_eui in self.mock_devs:
                lat = base_lat + random.uniform(-0.001, 0.001)
                lon = base_lon + random.uniform(-0.001, 0.001)
                rssi = random.randint(-110, -70)

                self.game_state.update_player_gps(dev_eui, lat, lon, rssi)

            time.sleep(8)

    def send_command(self, dev_eui, command_text):
        print(f" [MOCK SEND] Rozkaz '{command_text}' wysłany do {dev_eui}")
        return True


class MQTTHandler:
    # TUTAJ DODANO game_manager=None
    def __init__(self, game_state, game_manager=None):
        self.game_state = game_state
        self.game_manager = game_manager
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.downlink_topic = None

    def start(self):
        print(f"🌍 [MQTT] Łączenie z brokerem ({config.BROKER_IP}:{config.BROKER_PORT})...")
        self.client.connect(config.BROKER_IP, config.BROKER_PORT, 60)
        self.client.subscribe(config.TOPIC_UP)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_message(self, client, userdata, msg):
        try:
            if not self.downlink_topic:
                self.downlink_topic = msg.topic.replace("event/up", "command/down")

            payload = json.loads(msg.payload.decode('utf-8'))
            if "object" in payload:
                data = payload["object"]

                # Odbieramy EUI z prawidłowego indeksu [3]
                dev_eui = msg.topic.split("/")[3]

                lat = data.get("latitude") or data.get("lat")
                lon = data.get("longitude") or data.get("lon")
                rssi = payload.get("rxInfo", [{}])[0].get("rssi", -100)

                # Wyciągamy surowy kod od taga (jeśli nie ma, zakładamy 101 - PING)
                raw_code = data.get("kod", 101)

                # Tłumaczymy cyfrę na tekst (np. 101 -> "PING")
                event_type = config.UPLINK_MAP.get(raw_code, "UNKNOWN")

                # 1. Aktualizacja GPS (jeśli podano współrzędne)
                if lat is not None and lon is not None:
                    self.game_state.update_player_gps(dev_eui, lat, lon, rssi)

                # 2. Reakcja na konkretne zdarzenia
                if event_type == "PING":
                    print(f"🏓 [RADIO] PING od {dev_eui} | RSSI: {rssi}dBm")

                elif event_type == "HIT":
                    print(f"💀 [RADIO] Trafienie (Kod 102) od: {dev_eui}")
                    if self.game_manager:
                        self.game_manager.report_hit(dev_eui)

                elif event_type == "UNKNOWN":
                    print(f"❓ [RADIO] Nieznany kod ({raw_code}) od {dev_eui}")

        except Exception as e:
            print(f"Błąd przetwarzania MQTT: {e}")

    def send_command(self, dev_eui, command_text):
        if not self.downlink_topic:
            return False

        cmd_id = config.COMMAND_MAP.get(command_text)
        if cmd_id is None:
            return False

        # Generujemy temat dla konkretnego EUI
        topic = self.downlink_topic.replace("+", dev_eui)

        downlink_payload = {
            "devEui": dev_eui,
            "confirmed": False,
            "fPort": 1,
            "object": {
                "command_id": cmd_id
            }
        }

        result = self.client.publish(topic, json.dumps(downlink_payload))
        return result.rc == mqtt.MQTT_ERR_SUCCESS