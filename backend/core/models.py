# backend/core/models.py

class Player:
    def __init__(self, dev_eui):
        self.dev_eui = dev_eui
        self.is_alive = True
        self.team_name = None  # Na początku gracz nie ma drużyny

class Team:
    def __init__(self, name):
        self.name = name
        self.members = {}  # Słownik: dev_eui -> obiekt Player

    def add_player(self, player):
        player.team_name = self.name
        self.members[player.dev_eui] = player

    def remove_player(self, dev_eui):
        if dev_eui in self.members:
            self.members[dev_eui].team_name = None
            del self.members[dev_eui]

    @property
    def alive_count(self):
        return sum(1 for p in self.members.values() if p.is_alive)

    @property
    def total_count(self):
        return len(self.members)