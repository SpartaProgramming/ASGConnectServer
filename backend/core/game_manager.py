class GameManager:
    def __init__(self, state):
        self.state = state
        self.mqtt = None  # Podepniemy to w main.py
        self.is_running = False

    def set_mqtt(self, mqtt_handler):
        """Przekazujemy obiekt radia, żeby serwer mógł wysyłać komendy"""
        self.mqtt = mqtt_handler

    def start_game(self):
        self.is_running = True
        print("🟢 GRA WYSTARTOWAŁA!")

        for dev_eui, player_data in self.state.players.items():
            # Wszyscy ożywają na start
            player_data["is_alive"] = True
            # Wysyłamy fizyczny rozkaz odblokowania do każdego radia
            if self.mqtt:
                self.mqtt.send_command(dev_eui, "START")

        self.state.notify_callbacks(self.state.players)

    def stop_game(self):
        self.is_running = False
        print("🔴 GRA ZATRZYMANA!")

        for dev_eui in self.state.players:
            # Wysyłamy rozkaz blokady do każdego radia
            if self.mqtt:
                self.mqtt.send_command(dev_eui, "STOP")

    def reset_game(self):
        self.stop_game()
        print("🔄 GRA ZRESETOWANA!")
        for dev_eui, player_data in self.state.players.items():
            player_data["is_alive"] = True

        self.state.notify_callbacks(self.state.players)

    def report_hit(self, dev_eui):
        """Wywoływane przez radio (mqtt_handler.py) gdy wpłynie kod 102"""
        if not self.is_running:
            print(f"⚠️ Zignorowano trafienie: {dev_eui} dostał, ale gra nie jest uruchomiona.")
            return

        player = self.state.players.get(dev_eui)

        # Jeśli gracz istnieje i jest żywy -> zabijamy go
        if player and player.get("is_alive", True):
            player["is_alive"] = False
            print(f"💀 Gracz {dev_eui} został wyeliminowany!")

            # Od razu wysyłamy komendę do taga, żeby zablokował urządzenie/spust
            if self.mqtt:
                self.mqtt.send_command(dev_eui, "DEAD")

            # Aktualizujemy mapę na froncie Vue (zmieni kolor taga na szary/czerwony)
            self.state.notify_callbacks(self.state.players)

    def respawn_player(self, dev_eui):
        """Wywoływane przez admina z panelu Vue (lub z bazy medycznej)"""
        player = self.state.players.get(dev_eui)
        if player and not player.get("is_alive", True):
            player["is_alive"] = True
            print(f"⚕️ Gracz {dev_eui} wraca do gry!")

            # Wysyłamy komendę odblokowania do taga
            if self.mqtt:
                self.mqtt.send_command(dev_eui, "RESPAWN")

            self.state.notify_callbacks(self.state.players)