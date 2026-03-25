from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLineEdit)
from PyQt6.QtCore import Qt


class ASGGUI(QMainWindow):
    def __init__(self, game_state, mqtt_handler):
        super().__init__()
        self.game_state = game_state
        self.mqtt_handler = mqtt_handler

        self.setWindowTitle("Terminal Dowodzenia ASG - PyQt6")
        self.resize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- ZAKŁADKI ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_players = QWidget()
        self.tab_map = QWidget()
        self.tabs.addTab(self.tab_players, "Status Graczy")
        self.tabs.addTab(self.tab_map, "Mapa Taktyczna")

        # --- BUDOWA ZAKŁADKI GRACZY ---
        players_layout = QVBoxLayout(self.tab_players)

        # Profesjonalna tabela graczy
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["DevEUI", "Szerokość", "Długość", "Zasięg (dBm)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        players_layout.addWidget(self.table)

        # Pole do wysyłania komend
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Wpisz rozkaz (np. WSPARCIE)...")
        self.btn_send = QPushButton("Wyślij do wszystkich")

        cmd_layout.addWidget(self.cmd_input)
        cmd_layout.addWidget(self.btn_send)
        players_layout.addLayout(cmd_layout)

        self.game_state.state_updated.connect(self.refresh_table)

    def refresh_table(self):
        players = self.game_state.players
        self.table.setRowCount(len(players))

        row = 0
        for dev_eui, data in players.items():
            # Skracamy DevEUI dla czytelności
            short_eui = f"...{dev_eui[-4:]}"

            self.table.setItem(row, 0, QTableWidgetItem(short_eui))
            self.table.setItem(row, 1, QTableWidgetItem(str(data['lat'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(data['lon'])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{data['rssi']} dBm"))
            row += 1

    def closeEvent(self, event):
        print("Zamykanie systemu Qt...")
        self.mqtt_handler.stop()
        event.accept()