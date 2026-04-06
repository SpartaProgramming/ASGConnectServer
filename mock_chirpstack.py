import paho.mqtt.client as mqtt
import json
import time
import random
import threading

# --- Ustawienia LOKALNEGO brokera ---
BROKER_IP = "127.0.0.1"
BROKER_PORT = 1884
APP_ID = "1"

# Zamieniamy listę na słownik, żeby łatwiej wyciągać gracza po jego EUI
PLAYERS = {
    "Michal": {"lat": 50.10788, "lon": 17.03854},
    "Wiktor": {"lat": 53.10800, "lon": 13.03900},
    "Hubert": {"lat": 52.10800, "lon": 16.03900},
    "Maciek": {"lat": 55.10800, "lon": 17.03900},
    "KJU": {"lat": 49.10800, "lon": 17.03900},
    "Arek": {"lat": 52.10800, "lon": 17.03900},
}

# Słownik dostępnych komend (Tekst -> Surowy Kod)
CMD_TO_CODE = {
    "PING": 101,
    "HIT": 102,
    "SOS": 103
}


def on_connect(client, userdata, flags, rc):
    pass  # Ukrywamy logowanie, żeby nie śmieciło w konsoli podczas wpisywania komend


client = mqtt.Client()
client.on_connect = on_connect
client.connect(BROKER_IP, BROKER_PORT, 60)
client.loop_start()


def send_payload(dev_eui, lat, lon, code, silent=False):
    """Pomocnicza funkcja do budowania i wysyłania ramki JSON"""
    payload = {
        "deviceInfo": {"applicationId": APP_ID, "devEui": dev_eui},
        "rxInfo": [{"rssi": random.randint(-105, -70)}],
        "object": {
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "kod": code
        }
    }
    topic = f"application/{APP_ID}/device/{dev_eui}/event/up"
    client.publish(topic, json.dumps(payload))

    if not silent:
        print(f"\n✅ [TX] Wysłano kod {code} jako urządzenie {dev_eui}")


# ==========================================
# WĄTEK 1: Automatyczny GPS (Działa w tle)
# ==========================================
def background_gps_loop():
    while True:
        for dev_eui, p in PLAYERS.items():
            # Losowy ruch na mapie
            p["lat"] += random.uniform(-0.0001, 0.0001)
            p["lon"] += random.uniform(-0.0001, 0.0001)

            # Cicho wysyłamy PING (101) żeby utrzymać pozycję na serwerze
            send_payload(dev_eui, p["lat"], p["lon"], 101, silent=True)
        time.sleep(5)


gps_thread = threading.Thread(target=background_gps_loop, daemon=True)
gps_thread.start()

# ==========================================
# WĄTEK 2: Interaktywna konsola
# ==========================================
time.sleep(0.5)  # Krótka pauza, żeby broker zdążył się podłączyć przed rysowaniem menu

print("\n" + "=" * 50)
print("🎯 INTERAKTYWNY SYMULATOR URZĄDZEŃ")
print(f"Dostępne tagi: {list(PLAYERS.keys())}")
print(f"Dostępne akcje: {list(CMD_TO_CODE.keys())}")
print("Składnia: <AKCJA> <TAG> (np. HIT ABC111)")
print("Wpisz 'EXIT' aby zamknąć.")
print("=" * 50 + "\n")

try:
    while True:
        # Czekamy na komendę od użytkownika
        user_input = input(">> ").strip()

        if user_input == "EXIT":
            break
        if not user_input:
            continue

        parts = user_input.split()
        if len(parts) != 2:
            print("❌ Błąd składni. Użyj formatu: AKCJA TAG (np. HIT ABC111)")
            continue

        cmd, dev_eui = parts[0], parts[1]

        if cmd not in CMD_TO_CODE:
            print(f"❌ Nieznana akcja '{cmd}'. Wybierz z: {list(CMD_TO_CODE.keys())}")
            continue

        if dev_eui not in PLAYERS:
            print(f"❌ Nieznany tag '{dev_eui}'. Wybierz z: {list(PLAYERS.keys())}")
            continue

        # Pobieramy aktualne współrzędne tego gracza i wysyłamy ręczny pakiet
        current_pos = PLAYERS[dev_eui]
        code_to_send = CMD_TO_CODE[cmd]

        send_payload(dev_eui, current_pos["lat"], current_pos["lon"], code_to_send, silent=False)

except KeyboardInterrupt:
    pass
finally:
    print("\nZamykanie symulatora...")
    client.loop_stop()
    client.disconnect()