class GameState:
    def __init__(self):
        self.players = {}
        self.callbacks = []  # FastAPI will register a callback here

    def update_player_gps(self, dev_eui, lat, lon, rssi):
        if dev_eui not in self.players:
            self.players[dev_eui] = {"lat": 0, "lon": 0, "rssi": 0}
        self.players[dev_eui].update({"lat": lat, "lon": lon, "rssi": rssi})
        self.notify_callbacks(self.players)  # Używamy nowej metody

        # Notify the FastAPI server that data changed!
        for callback in self.callbacks:
            callback(self.players)

    def notify_callbacks(self, data):
        for callback in self.callbacks:
            callback(data)

