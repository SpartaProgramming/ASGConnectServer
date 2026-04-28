import paho.mqtt.client as mqtt
import json
import config
import time

class MQTTHandler:
    def __init__(self, game_session,registry):
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.game_session = game_session
        self.registry = registry
        self.downlink_topic = "application/{app_id}/device/{dev_eui}/command/down"
        self.current_app_id = "6de6c9b4-ead7-475a-8ad7-2034e22ce6ed"

    def start(self):
        print(f"[MQTT] Łączenie z brokerem ({config.BROKER_IP}:{config.BROKER_PORT})...")
        self.client.connect(config.BROKER_IP, config.BROKER_PORT, 60)
        self.client.subscribe("application/+/device/+/event/up")
        self.client.loop_start() #uruchamia wątek w tle
        print("[MQTT] Połączono i zasubskrybowano!")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    """
        Obsługuje odebranie uplinku z serwera ChirpStack
    """
    def on_message(self, client, userdata, msg):
        try:
            print(f"[MQTT] Otrzymano uplink: {msg.topic} | Payload: {msg.payload.decode('utf-8')}")
            parts = msg.topic.split("/")
            #self.current_app_id = parts[1]
            dev_eui = parts[3].upper()

            payload = json.loads(msg.payload.decode('utf-8'))

            rx_info = payload.get("rxInfo", [{}])[0]
            rssi = rx_info.get("rssi", -120)
            snr = rx_info.get("snr", 0.0)

            game_data = payload.get("object", {})

            # 1. Zawsze aktualizuj dane sprzętowe (nawet bez sesji)
            tag = self.registry.get_tag(dev_eui)
            if tag:
                tag.update_metrics(rssi, snr)
                tag.last_seen = time.time()
                tag.status = "ONLINE"

            # 2. Przekaż do sesji tylko jeśli ona ISTNIEJE i DZIAŁA
            if self.game_session and getattr(self.game_session, 'is_running', False):
                self.game_session.process_incoming_event(dev_eui, game_data, rssi, snr)
            else:
                # Opcjonalnie loguj tylko TELEMETRY, żeby nie spamować konsoli
                if game_data.get("type") == "TELEMETRY":
                    print(f"[MQTT] {dev_eui} wysłał pozycję, ale gra nie trwa.")
        except Exception as e:
            print(f"[MQTT] Błąd przetwarzania: {e}")

    # =======================================================
    # FUNKCJE WYSYŁAJĄCE (DOWNLINKI)
    # =======================================================
    def _send_downlink(self, dev_eui, payload_object, f_port=1, confirmed=False):
        if not self.current_app_id:
            print("[MQTT] Błąd: Brak AppID (czekam na pierwszy uplink od dowolnego taga)")
            return

        topic = self.downlink_topic.format(app_id=self.current_app_id, dev_eui=dev_eui)
        msg = {
            "devEui": dev_eui,
            "confirmed": False,
            "fPort": f_port,
            "object": payload_object
        }
        self.client.publish(topic, json.dumps(msg))

    def send_config(self, dev_eui, token, team, game_type, time_mins, allies_tot, enemies_tot, nickname):
        print(f"[MQTT] Konfiguruję gracza {dev_eui} ({nickname}) | Token: {token}")
        self._send_downlink(dev_eui, {
            "cmd": "CONFIG",
            "token": token,
            "team": team,
            "gameType": int(game_type),
            "timeMinutes": int(time_mins),
            "alliesTotal": int(allies_tot),
            "enemiesTotal": int(enemies_tot),
            "nickname": str(nickname)[:10]
        }, f_port=1, confirmed=False)

    def send_command(self, dev_eui, token, command_id):
        print(f"[MQTT] Komenda '{command_id}' wysyłana do {dev_eui} | Token: {token}")
        self._send_downlink(dev_eui, {
            "cmd": "COMMAND",
            "token": token,
            "val": command_id
        }, f_port=1, confirmed=False)

    def send_update(self, dev_eui, allies_alive, enemies_alive):
        self._send_downlink(dev_eui, {
            "cmd": "UPDATE",
            "alliesAlive": int(allies_alive),
            "enemiesAlive": int(enemies_alive)
        }, f_port=1, confirmed=False)