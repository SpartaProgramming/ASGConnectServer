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
    def __init__(self, game_state):
        self.game_state = game_state
        self.running = False
        self.thread = None
        # Symulujemy kilka urządzeń
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
        # Startowe współrzędne (np. środek poligonu)
        base_lat = 51.10788
        base_lon = 17.03854

        while self.running:
            for dev_eui in self.mock_devs:
                # Dodajemy losowy "szum" do pozycji, żeby marker się ruszał
                lat = base_lat + random.uniform(-0.001, 0.001)
                lon = base_lon + random.uniform(-0.001, 0.001)
                rssi = random.randint(-110, -70)

                self.game_state.update_player_gps(dev_eui, lat, lon, rssi)

            time.sleep(8)

    def send_command(self, dev_eui, command_text):
        print(f" [MOCK SEND] Rozkaz '{command_text}' wysłany do {dev_eui}")
        return True

class MQTTHandler:
    def __init__(self, game_state):
        self.game_state = game_state #aktualizuj game_state a nie GUI
        self.client = mqtt.Client()
        self.client.on_message = self.on_message #callback
        self.downlink_topic = None

    def start(self):
        self.client.connect(config.BROKER_IP, 1883, 60)
        self.client.subscribe(config.TOPIC_UP)
        self.client.loop_start() #uruchom w osobnym wątku

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

                dev_eui = msg.topic.split("/")[4] # bo application/1/device/ABC123/event/up

                if data.get("type") == "gps":
                    self.game_state.update_player_gps(
                        dev_eui, data["latitude"], data["longitude"],
                        payload.get("rxInfo", [{}])[0].get("rssi", "---")
                    )
        except Exception as e:
            print(f"Błąd MQTT: {e}")

    def send_command(self, dev_eui, command_text):
        if not self.downlink_topic:
            return False

        cmd_id = config.COMMAND_MAP.get(command_text)
        if cmd_id is None:
            return False

        downlink_payload = {
            "devEui": dev_eui,
            "confirmed": False,
            "fPort": 1,
            "object": {
                "command_id": cmd_id
            }
        }

        result = self.client.publish(self.downlink_topic, json.dumps(downlink_payload))

        return result.rc == mqtt.MQTT_ERR_SUCCESS