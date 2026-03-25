import sys
from PyQt6.QtWidgets import QApplication
from core.game_state import GameState
from core.mqtt_handler import MQTTHandler
from ui.gui_app import ASGGUI


def run_gui():
    # 1. Inicjalizacja środowiska Qt (musi być pierwsza!)
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    # 2. Inicjalizacja naszej logiki
    state = GameState()
    mqtt = MQTTHandler(state)
    mqtt.start()

    # 3. Odpalenie okna
    window = ASGGUI(state, mqtt)
    window.show()

    # 4. Uruchomienie głównej pętli programu
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()