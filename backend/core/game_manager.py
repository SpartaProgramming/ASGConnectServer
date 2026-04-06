# backend/core/game_manager.py
from .models import Player, Team
from .game_modes import Deathmatch

class GameManager:
    def __init__(self, state): # <--- DODANO 'state'
        self.state = state     # <--- ZAPISUJEMY 'state'
        self.players_pool = {}
        self.teams = {
            "RED": Team("RED"),
            "BLUE": Team("BLUE")
        }
        self.active_mode = None


    def register_device(self, dev_eui):
        """Ktoś włączył urządzenie na poligonie - dodajemy go do puli."""
        if dev_eui not in self.players_pool:
            self.players_pool[dev_eui] = Player(dev_eui)

    def assign_to_team(self, dev_eui, team_name):
        """Przydzielanie gracza do drużyny z zabezpieczeniem (usunięcie z poprzedniej)."""
        if dev_eui not in self.players_pool:
            return  # Nie ma takiego urządzenia

        player = self.players_pool[dev_eui]

        # 1. Usuń z obecnych drużyn (żeby nie był podwójnym agentem)
        for t in self.teams.values():
            t.remove_player(dev_eui)

        # 2. Dodaj do nowej drużyny
        if team_name in self.teams:
            self.teams[team_name].add_player(player)

    def start_game(self, mode_name):
        """Rozpoczyna wybraną grę."""
        # Wskrzeszamy wszystkich przed startem
        for p in self.players_pool.values():
            p.is_alive = True

        if mode_name == "Deathmatch":
            self.active_mode = Deathmatch(self.teams)
            print("[SZTAB] Rozpoczęto Team Deathmatch!")

    def report_hit(self, dev_eui):
        """Odbiera sygnał HIT z radia i przekazuje do logiki gry."""
        if self.active_mode and self.active_mode.is_running:
            self.active_mode.process_hit(dev_eui)