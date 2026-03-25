import paho.mqtt.client as mqtt
import json
import config


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

        # Budujemy strukturę, którą Twój Codec JS rozpakuje
        downlink_payload = {
            "devEui": dev_eui,
            "confirmed": False,
            "fPort": 1,
            "object": {
                "command_id": cmd_id  # To trafi do funkcji encodeDownlink w JS
            }
        }

        # Wysyłamy do brokera
        result = self.client.publish(self.downlink_topic, json.dumps(downlink_payload))

        # Sprawdzamy, czy wysyłka do brokera się udała
        return result.rc == mqtt.MQTT_ERR_SUCCESS