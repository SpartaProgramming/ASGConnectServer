import uuid


class PlayerProfile:
    def __init__(self, nickname, player_id=None, rank=None, role=None):
        self.player_id = player_id if player_id else str(uuid.uuid4())[:8]
        self.nickname = nickname
        self.rank = rank
        self.role = role
        self.games_played = 0
        self.killed_count = 0
        self.total_distance_km = 0.0

    def add_game_stats(self, distance):
        self.total_distance_km += distance
        self.games_played += 1

    def to_dict(self):
        return {
            "id": self.player_id,
            "nick": self.nickname,
            "rank": self.rank,
            "role": self.role,
            "games_count": self.games_played,
            "killed_count": self.killed_count
        }

    def __repr__(self):
        return f"<PlayerProfile {self.nickname} | ID: {self.player_id} | Role: {self.role}>"
