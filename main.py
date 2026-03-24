import customtkinter as ctk
import paho.mqtt.client as mqtt
import json

# --- KONFIGURACJA ---
BROKER_IP = "10.0.0.72"
TOPIC_UP = "application/+/device/+/event/up"
DEV_EUI = "e082243450f29654"


class ASGCommandCenter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Terminal Dowodzenia ASG")
        self.geometry("500x400")
        ctk.set_appearance_mode("dark")

        # Zmienna przechowująca autowykryty temat do wysyłania
        self.downlink_topic = None

        # --- UI ---
        self.label_title = ctk.CTkLabel(self, text="STATUS GRACZA", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=10)

        self.coords_label = ctk.CTkLabel(self, text="Koordynaty: Czekam na dane...", font=("Arial", 16))
        self.coords_label.pack(pady=5)

        self.rssi_label = ctk.CTkLabel(self, text="Sygnał: --- dBm", font=("Arial", 12))
        self.rssi_label.pack(pady=5)

        self.topic_label = ctk.CTkLabel(self, text="Temat: Wyszukiwanie...", text_color="orange")
        self.topic_label.pack(pady=5)

        self.entry = ctk.CTkEntry(self, placeholder_text="Wpisz rozkaz (np. WSPARCIE)...", width=300)
        self.entry.pack(pady=20)

        self.send_button = ctk.CTkButton(self, text="WYŚLIJ ROZKAZ", command=self.send_downlink, state="disabled")
        self.send_button.pack(pady=10)

        # --- MQTT Setup ---
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(BROKER_IP, 1883, 60)
        self.client.subscribe(TOPIC_UP)
        self.client.loop_start()

    def on_message(self, client, userdata, msg):
        try:
            # 1. AUTO-WYKRYWANIE TEMATU:
            # Temat msg.topic wygląda np. tak: application/993c8309-8d13.../device/e082243450f29654/event/up
            if not self.downlink_topic:
                # Zamieniamy "event/up" na "command/down"
                self.downlink_topic = msg.topic.replace("event/up", "command/down")
                print(f"✅ Znaleziono poprawny temat: {self.downlink_topic}")

                # Aktualizujemy UI i odblokowujemy przycisk wysyłania
                self.topic_label.configure(text="Temat: Gotowy do wysyłania!", text_color="green")
                self.send_button.configure(state="normal")

            # 2. ODCZYT DANYCH Z TAGA:
            payload = json.loads(msg.payload.decode('utf-8'))

            if "object" in payload:
                data = payload["object"]

                # Upewniamy się, że to nasz zdekodowany pakiet GPS
                if data.get("type") == "gps":
                    lat = data.get("latitude")
                    lon = data.get("longitude")
                    rssi = payload.get("rxInfo", [{}])[0].get("rssi", "---")

                    self.coords_label.configure(text=f"Koordynaty: {lat}, {lon}")
                    self.rssi_label.configure(text=f"Sygnał: {rssi} dBm")
                    print(f"Odebrano pozycję: {lat}, {lon}")

                elif data.get("type") == "ping":
                    print("Odebrano Ping (otwarcie okna RX)")

        except Exception as e:
            print(f"Błąd przetwarzania wiadomości: {e}")

    def send_downlink(self):
        message = self.entry.get()
        if not message or not self.downlink_topic:
            return

        # Używamy naszego skryptu Codec w panelu ChirpStack (zmienna "object")
        # ChirpStack samodzielnie zajmie się Base64
        downlink_payload = {
            "devEui": DEV_EUI,  # Ważne: ChirpStack v4 wymaga tego pola wewnątrz JSONa
            "confirmed": False,
            "fPort": 1,
            "object": {
                "command": message
            }
        }

        # Publikacja do brokera MQTT
        self.client.publish(self.downlink_topic, json.dumps(downlink_payload))
        print(f"Wysłano do kolejki ChirpStacka: {message}")
        self.entry.delete(0, 'end')


if __name__ == "__main__":
    app = ASGCommandCenter()
    app.mainloop()