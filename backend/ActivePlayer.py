"""
    Cyfrowy bliźniak na czas rozgrywki. Łączy w sobie dane z profilu gracza,
     obiekt taga, status, pozycję, przynależność do drużyny.
"""
class ActivePlayer:
    def __init__(self, device_tag, profile=None, team=None):
        self.profile = profile
        self.tag = device_tag
        self.team = team
        self.status = "ALIVE"
        self.lat, self.lon = 0.0, 0.0

        self.state = {
            "hp": 100,
            "respawns": 0,
            "captured_flags": 0,
            "is_in_base": False
        }

    def apply_hit(self):
        self.status = "DEAD"
        return self.tag.generate_new_token()