# config.py

# DOWNLINK: Serwer -> Tag (co wysyłamy z Vue)
COMMAND_MAP = {
    "WSPARCIE": 1,
    "ODWROT": 2,
    "ATAK": 3,
    "ZBIORKA": 4,
    "PING": 99,
    "START": 10,     # Odblokuj tagi, rozpocznij grę
    "STOP": 11,      # Zablokuj wszystkie tagi (np. koniec czasu)
    "DEAD": 12,      # Wymuś zablokowanie taga (gracz oberwał)
    "RESPAWN": 13    # Odblokuj taga (medyk lub admin przywrócił do gry)
}

# UPLINK: Tag -> Serwer (co przysyła urządzenie)
UPLINK_MAP = {
    101: "PING", # Zwykłe zgłoszenie obecności/pozycji
    102: "HIT",  # Gracz dostał
    103: "SOS"   # Przykład: gracz wzywa pomoc medyczną
}

# ==========================================
# WYBÓR ŚRODOWISKA (Odkomentuj właściwe)
# ==========================================

# 1. TRYB DOMOWY (Lokalny broker Mosquitto na porcie 1884)
BROKER_IP = "127.0.0.1"
BROKER_PORT = 1884

# 2. TRYB POLIGON (Prawdziwy ChirpStack przez WiFi/LAN)
# BROKER_IP = "10.0.0.72"
# BROKER_PORT = 1883

# ==========================================
# KONFIGURACJA MQTT
# ==========================================
TOPIC_UP = "application/+/device/+/event/up"
COMMAND_MAP = {"WSPARCIE": 1, "ODWROT": 2, "ATAK": 3, "ZBIORKA": 4}
USE_MOCK = False