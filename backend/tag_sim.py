#!/usr/bin/env python3
import argparse
import json
import random
import threading
import time
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER = "10.0.0.5"
PORT = 1883

class TagSimulator:
    def __init__(self, app_id, dev_eui, lat, lon):
        self.app_id = app_id
        self.dev_eui = dev_eui
        self.lat = lat
        self.lon = lon
        self.running = True

        self.nickname = "WAITING..."
        self.team = "NONE"
        self.phase = "SETUP"
        self.allies_alive = 0
        self.enemies_alive = 0
        self.time_left = 0

        self.client = mqtt.Client(client_id=f"Sim_{dev_eui}")
        self.client.on_message = self.on_message

        self.up_topic = f"application/{app_id}/device/{dev_eui}/event/up"
        self.down_topic = f"application/{app_id}/device/{dev_eui}/command/down"

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            # ChirpStack przesyła dane z serwera w polu "object"
            if "object" in payload:
                data = payload["object"]
                cmd = data.get("cmd")

                if cmd == "CONFIG":
                    self.nickname = data.get("nickname")
                    self.team = data.get("team")
                    self.time_left = data.get("timeMinutes") * 60
                    self.allies_alive = data.get("alliesTotal")
                    self.enemies_alive = data.get("enemiesTotal")
                    self.phase = "READY"
                    print(f"\n[TAG] Otrzymano CONFIG: Nick={self.nickname}, Team={self.team}")

                elif cmd == "COMMAND":
                    val = data.get("val")
                    if val == "START":
                        self.phase = "RUNNING"
                        print("\n[TAG] GRA WYSTARTOWAŁA!")
                    elif val == "DIE":
                        print("\n[TAG] ZOSTAŁEŚ ZABITY (DIE)!")

                elif cmd == "UPDATE":
                    self.allies_alive = data.get("alliesAlive")
                    self.enemies_alive = data.get("enemiesAlive")
                    print(f"\n[TAG] UPDATE: Sojusznicy: {self.allies_alive}, Wrogowie: {self.enemies_alive}")

                self.print_screen()
        except Exception as e:
            print(f"Błąd odbioru: {e}")

    def print_screen(self):
        """Symulacja ekranu TFT"""
        print("\n" + "=" * 30)
        print(f" EKRAN TAGA: {self.dev_eui}")
        print(f" Gracz: {self.nickname} | Team: {self.team}")
        print(f" Faza: {self.phase} | Czas: {self.time_left // 60:02d}:{self.time_left % 60:02d}")
        print(f" Żywi - My: {self.allies_alive} | Oni: {self.enemies_alive}")
        print("=" * 30 + "\n> ", end="")

    def send_telemetry(self):
        while self.running:
            if self.phase == "RUNNING":
                # Symulacja ruchu
                self.lat += random.uniform(-0.0001, 0.0001)
                self.lon += random.uniform(-0.0001, 0.0001)
                if self.time_left > 0: self.time_left -= 10

            payload = {
                "object": {
                    "type": "TELEMETRY",
                    "lat": round(self.lat, 6),
                    "lon": round(self.lon, 6)
                }
            }
            self.client.publish(self.up_topic, json.dumps(payload))
            time.sleep(10)

    def send_ping(self):
        # Struktura identyczna z tą, którą generuje ChirpStack Gateway Bridge
        payload = {
            "devEUI": self.dev_eui,
            "applicationID": self.app_id,
            "rxInfo": [{
                "rssi": -50,
                "snr": 10.0
            }],
            "object": {
                "type": "PING"
            }
        }
        # Publikujemy na ten sam topic, na którym "słucha" serwer
        self.client.publish(self.up_topic, json.dumps(payload))
        print(f"[SIM] Wysłano symulowany pakiet Gatewaya dla {self.dev_eui}")

    def send_killed(self):
        payload = {"object": {"type": "KILLED"}}
        self.client.publish(self.up_topic, json.dumps(payload))
        print(f"\n[TAG] Wysłano zdarzenie KILLED (naciśnięto przycisk)")

    def run(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.subscribe(self.down_topic)
        self.client.loop_start()

        # --- KLUCZOWA ZMIANA ---
        # Daj mu sekundę na ustabilizowanie połączenia i wyślij PING
        time.sleep(1)
        self.send_ping()
        # ------------------------

        # Wątek telemetrii
        threading.Thread(target=self.send_telemetry, daemon=True).start()

        print(f"Symulator uruchomiony. DevEUI: {self.dev_eui}")
        print("Komendy: 'p' - wyślij PING, 'k' - wyślij KILLED, 'q' - wyjdź")

        while self.running:
            cmd = input("> ").lower().strip()
            if cmd == 'k':
                self.send_killed()
            elif cmd == 'p':  # Dodaj ręczne wysyłanie PINGa dla testów
                self.send_ping()
            elif cmd == 'q':
                self.running = False


if __name__ == "__main__":
    # Uruchomienie: podaj ID aplikacji z ChirpStack i DevEUI taga
    # Musi być zgodne z tym, co wpisujesz w serwerze!
    TAG_EUI = "E082243450F29658"
    APP_ID = "1"

    sim = TagSimulator(APP_ID, TAG_EUI, 51.107, 17.038)
    sim.run()