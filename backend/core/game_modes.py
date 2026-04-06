# backend/core/game_modes.py

class Deathmatch:
    def __init__(self, teams):
        """
        teams: słownik obiektów Team, np. {"RED": <Team object>, "BLUE": <Team object>}
        """
        self.name = "Team Deathmatch"
        self.teams = teams
        self.is_running = True

    def process_hit(self, victim_eui):
        """Ktoś dostał kulką. Szukamy go w drużynach i zmieniamy status na martwy."""
        if not self.is_running:
            return False

        for team in self.teams.values():
            if victim_eui in team.members:
                player = team.members[victim_eui]
                if player.is_alive:
                    player.is_alive = False
                    self._check_win_condition() # Sprawdzamy czy to był ostatni żywy
                    return True
        return False

    def _check_win_condition(self):
        """Sprawdza, czy któraś drużyna nie ma już żywych graczy."""
        alive_teams = []
        for team_name, team in self.teams.items():
            if team.alive_count > 0:
                alive_teams.append(team_name)

        if len(alive_teams) <= 1:
            self.is_running = False
            winner = alive_teams[0] if alive_teams else "REMIS"
            print(f"\n[SĘDZIA] Koniec gry! Zwycięża drużyna: {winner}")

    def get_stats(self):
        """Zwraca suchy raport z pola walki"""
        stats = {}
        for team_name, team in self.teams.items():
            stats[team_name] = f"{team.alive_count} / {team.total_count} żywych"
        return stats