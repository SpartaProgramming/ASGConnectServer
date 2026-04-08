import logging
from .database import log_hit_to_db # . szukaj w tym samym folderze

class GameManager:
    def __init__(self, state):
        self.state = state
        self.mqtt = None
        self.is_running = False

    def set_mqtt(self, mqtt_handler):
        self.mqtt = mqtt_handler

    def start_game(self):
        self.is_running = True
        print("GRA WYSTARTOWAŁA!")

        for dev_eui, player_data in self.state.players.items():
            # Wszyscy ożywają na start
            player_data["is_alive"] = True
            # Wysyłamy fizyczny rozkaz odblokowania do każdego radia
            if self.mqtt:
                self.mqtt.send_command(dev_eui, "START")

        self.state.notify_callbacks(self.state.players)

    def stop_game(self):
        self.is_running = False
        print("GRA ZATRZYMANA!")

        for dev_eui in self.state.players:
            if self.mqtt:
                self.mqtt.send_command(dev_eui, "STOP")

    def reset_game(self):
        self.stop_game()
        print("GRA ZRESETOWANA!")
        for dev_eui, player_data in self.state.players.items():
            player_data["is_alive"] = True

        self.state.notify_callbacks(self.state.players)

    def report_hit(self, dev_eui):
            if not self.is_running:
                logging.warning(f"Zignorowano trafienie {dev_eui} - gra nie trwa.")
                return

            player = self.state.players.get(dev_eui)
            if player and player.get("is_alive", True):
                player["is_alive"] = False
                logging.info(f"💀 TRAFIENIE: {dev_eui} wyeliminowany.")

                # Zapis do bazy danych
                log_hit_to_db(dev_eui)

                if self.mqtt:
                    self.mqtt.send_command(dev_eui, "DEAD")

                self.state.notify_callbacks(self.state.players)

    def respawn_player(self, dev_eui):
        player = self.state.players.get(dev_eui)
        if player and not player.get("is_alive", True):
            player["is_alive"] = True
            print(f"⚕️ Gracz {dev_eui} wraca do gry!")

            # Wysyłamy komendę odblokowania do taga
            if self.mqtt:
                self.mqtt.send_command(dev_eui, "RESPAWN")

            self.state.notify_callbacks(self.state.players)

