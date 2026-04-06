import asyncio
import time


class GameManager:
    def __init__(self, state):
        self.state = state
        self.is_running = False
        self.start_time = None
        self.game_type = "TDM"  # Domyślnie Team Deathmatch
        self.duration = 3600  # 1 godzina w sekundach
        self.teams = {
            "RED": [],
            "BLUE": []
        }
        self.scores = {"RED": 0, "BLUE": 0}

    def setup_game(self, game_type, duration):
        self.game_type = game_type
        self.duration = duration
        self.scores = {"RED": 0, "BLUE": 0}
        print(f"📡 Gra ustawiona: {game_type}, czas: {duration}s")

    def assign_to_team(self, dev_eui, team):
        # Usuń z innych drużyn i dodaj do wybranej
        for t in self.teams:
            if dev_eui in self.teams[t]:
                self.teams[t].remove(dev_eui)
        if team in self.teams:
            self.teams[team].append(dev_eui)

    async def run_game_loop(self):
        self.is_running = True
        self.start_time = time.time()
        while self.is_running:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.duration - elapsed)

            # Wysyłamy status gry do frontendu przez GameState
            game_status = {
                "type": "GAME_UPDATE",
                "data": {
                    "is_running": self.is_running,
                    "remaining_time": int(remaining),
                    "scores": self.scores,
                    "teams": self.teams,
                    "game_type": self.game_type
                }
            }
            self.state.notify_callbacks(game_status)

            if remaining <= 0:
                self.is_running = False

            await asyncio.sleep(1)  # Odświeżanie zegara gry co sekundę