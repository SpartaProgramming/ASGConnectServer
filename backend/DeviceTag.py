import time

"""
Klasa reprezentująca pojedynczy TAG.
"""
class DeviceTag:
    def __init__(self, dev_eui):
        self.dev_eui = dev_eui.upper()

        self.status = "DISCONNECTED"  # ONLINE, TIMEOUT, DISCONNECTED
        self.last_seen = 0.0  # Timestamp ostatniego odebranego pakietu

        self.rssi = 0  # Siła sygnału (np. -95 dBm)
        self.snr = 0.0  # Jakość sygnału (np. 7.5 dB)
        self.uplink_count = 0  # Licznik odebranych pakietów
        self.downlink_count = 0  # Licznik wysłanych pakietów

        self.battery_voltage = 0.0  # Napięcie (jeśli wysyłane w object lub metrics)

        # --- LOGIKA SYNCHRONIZACJI (Digital Twin) ---
        self.is_synced = False  # Czy stan Taga jest zgodny z serwerem?
        self.pending_token = 0  # Numer aktualnie wysłanej transakcji
        self.last_sync_attempt = 0.0  # Czas ostatniej wysyłki CONFIG
        self.queue_status = "IDLE"  # IDLE, PENDING_ACK

    def update_metrics(self, rssi, snr, battery=None):
        self.last_seen = time.time()
        self.status = "ONLINE"
        self.uplink_count += 1
        self.rssi = rssi
        self.snr = snr

        if battery is not None:
            self.battery_voltage = battery

    def generate_new_token(self):
        self.pending_token = (self.pending_token + 1) % 256
        self.is_synced = False
        self.queue_status = "PENDING_ACK"
        self.last_sync_attempt = time.time()
        return self.pending_token

    def confirm_ack(self, received_token):
        if self.pending_token == received_token:
            self.is_synced = True
            self.queue_status = "IDLE"
            print(f"[TAG {self.dev_eui}] Synchronizacja OK (Token: {received_token})")
            return True
        else:
            print(f"[TAG {self.dev_eui}] Otrzymano nieaktualny token: {received_token}")
            return False

    def check_connection(self, timeout_seconds=120):
        if self.status == "ONLINE":
            if (time.time() - self.last_seen) > timeout_seconds:
                self.status = "TIMEOUT"
                return True
        return False

    def get_technical_status(self):
        return {
            "devEui": self.dev_eui,
            "status": self.status,
            "rssi": f"{self.rssi} dBm",
            "snr": f"{self.snr} dB",
            "battery": f"{self.battery_voltage}V",
            "synced": self.is_synced,
            "lastSeen": time.strftime('%H:%M:%S', time.localtime(self.last_seen))
        }

    def __repr__(self):
        sync_symbol = "✔" if self.is_synced else "✘"
        return f"<DeviceTag {self.dev_eui} [{self.status}] Sync:{sync_symbol} RSSI:{self.rssi}>"