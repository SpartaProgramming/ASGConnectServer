from mqtt_handler import MQTTHandler
from GameSession import GameSession
from GameMode import GameMode, TeamDeathmatch
from DeviceRegistry import DeviceRegistry
from PlayerProfile import PlayerProfile
import pickle

"""
    Tworzenie trybów gry: ID, nazwa, klasa_trybu
    Factory Method, Strategy Pattern - wybór trybu gry w locie, bez konieczności modyfikacji kodu ASGConnect.py
"""
class GameModeFactory:
    @staticmethod
    def get_available_modes():
        return {
            "1": ("Team Deathmatch", TeamDeathmatch),
            "2": ("Capture the Flag", GameMode),
            "3": ("King of the Hill", GameMode),
        }

    @staticmethod
    def choose_mode(mode_id): #dynamiczne tworzenie obiektów na podstawie ID trybu
        modes = GameModeFactory.get_available_modes()
        if mode_id in modes:
            name, cls = modes[mode_id]
            return cls(name=name) # tworzy instancję odpowiedniej klasy trybu
        return TeamDeathmatch(name="Team Deathmatch") # zwraca domyślny tryb gry

"""
   Główna klasa zarządzająca całym systemem. Odpowiada za:
- Zarządzanie rejestrem urządzeń (DeviceRegistry)
- Zarządzanie sesją gry (GameSession)
- Zarządzanie trybem gry (GameMode)
- Zarządzanie profilami graczy (PlayerProfile)
- Integrację z MQTT (MQTTHandler)
- Zapewnienie interfejsu do operacji na profilach i trybach gry (np. z web_server.py)
"""
class ASGConnect:
    def __init__(self):
        self.registry = DeviceRegistry()
        self.mode = None
        self.session = None
        self.mqtt = None
        self.profiles = self.load_profiles()

    def load_profiles(self):
        try:
            with open('profiles.pkl', 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    def save_profiles(self):
        with open('profiles.pkl', 'wb') as f:
            pickle.dump(self.profiles, f)

    """
        Inicjalziacja Gry, wybór trybu rozgrywki, tworzenie sesji, integracja z MQTT.
        Wymaga właściwej koljności inicjalizacji obiektów(cykliczna zależność konstruktorów).
        Two-phase initialization, Dependency Injection
    """

    def prepare_game(self, mode_id="1"):
        self.mode = GameModeFactory.choose_mode(mode_id)
        print(f"[SERVER] Tryb {self.mode.name} przygotowany.")


    def start(self):
        if not self.mode:
            self.prepare_game("1")

        # Inicjalizacja Sesji
        self.session = GameSession(
            mqtt_handler=None,
            game_mode=self.mode,
            registry=self.registry,
            asg_app=self
        )

        # Inicjalizacja MQTT
        self.mqtt = MQTTHandler(game_session=self.session, registry=self.registry)
        self.session.mqtt = self.mqtt
        self.mqtt.start()

        # Uruchomienie logiki rundy
        self.session.start_round()
        print("[SERVER] SESJA I MQTT URUCHOMIONE.")

    def stop(self):
        if self.mqtt:
            self.mqtt.stop()
        print("[SERVER] System zatrzymany.")

    def add_profile(self, nickname, role="Rekrut"):
        profile = PlayerProfile(nickname=nickname, role=role)
        self.profiles[profile.player_id] = profile
        self.save_profiles()
        return profile

    def edit_profile(self, profile_id, nickname=None, role=None):
        if profile_id in self.profiles:
            if nickname:
                self.profiles[profile_id].nickname = nickname
            if role:
                self.profiles[profile_id].role = role
            self.save_profiles()
            return True
        return False

    def delete_profile(self, profile_id):
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            self.save_profiles()
            return True
        return False

    def get_profiles(self):
        return {pid: p.to_dict() for pid, p in self.profiles.items()}

    def send_config_to_all(self):
        """Wysyła konfigurację do wszystkich zarejestrowanych graczy"""
        for player in self.registry.get_all_players():
            self.session.sync_player(player)
