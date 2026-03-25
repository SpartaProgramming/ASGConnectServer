from PyQt6.QtCore import QObject, pyqtSignal


class GameState(QObject):
    state_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.players = {}
        self.game_mode = "LOBBY"

    def update_player_gps(self, dev_eui, lat, lon, rssi):
        if dev_eui not in self.players:
            self.players[dev_eui] = {"lat": 0, "lon": 0, "rssi": 0, "status": "OK"}

        self.players[dev_eui]["lat"] = lat
        self.players[dev_eui]["lon"] = lon
        self.players[dev_eui]["rssi"] = rssi

        self.state_updated.emit()