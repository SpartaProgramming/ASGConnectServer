import logging
from .database import log_hit_to_db # . szukaj w tym samym folderze

class GameManager:
    def __init__(self, state):
        self.state = state
        self.mqtt = None
        self.is_running = False
        self.current_match = None # obiekt Rozgrywki

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

    def report_hit(self, victim_eui):
        """Metoda wywoływana przez MQTT Handler"""
        if not self.is_running:
            logging.warning(f"Gra nie trwa, trafienie {victim_eui} zignorowane.")
            return

        logging.info(f"💥 [RADIO] Trafienie od: {victim_eui}")

        # 1. Przekaż trafienie do logiki Deathmatch
        if self.current_match:
            hit_successful = self.current_match.process_hit(victim_eui)

            if hit_successful:
                # 2. Zapisz do bazy danych
                log_hit_to_db(victim_eui)

                # 3. Zaktualizuj stan ogólny dla Frontendu
                if victim_eui in self.state.players:
                    self.state.players[victim_eui]["is_alive"] = False

                # 4. Wyślij rozkaz DEAD do taga
                if self.mqtt:
                    self.mqtt.send_command(victim_eui, "DEAD")

                # 5. Sprawdź czy gra się skończyła w obiekcie Deathmatch
                if not self.current_match.is_running:
                    self.stop_game()
                    logging.info("🏆 KONIEC GRY - Wykryto zwycięzcę!")

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

