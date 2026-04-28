# ==========================================
# KONFIGURACJA POŁĄCZENIA Z CHIRPSTACK
# ==========================================

BROKER_IP = "10.0.0.5"
BROKER_PORT = 1883

# Nasłuchujemy zdarzeń ze wszystkich aplikacji i wszystkich urządzeń
TOPIC_UP = "application/+/device/+/event/up"