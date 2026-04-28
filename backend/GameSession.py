import time
from DeviceTag import DeviceTag
from PlayerProfile import PlayerProfile
from ActivePlayer import ActivePlayer

class GameSession:
    def __init__(self, mqtt_handler, game_mode, registry, asg_app):
        self.mqtt = mqtt_handler
        self.mode = game_mode
        self.registry = registry
        self.asg_app = asg_app
        self.start_time = None
        self.is_running = False
        self.status = 'configuration'
        self.time_left = 0

    def add_player(self, active_player_obj):
        """Rejestruje gracza w globalnym rejestrze"""
        self.registry.link_player(active_player_obj)
        print(f"[GAME] Zarejestrowano: {active_player_obj.profile.nickname}")

    def start_round(self, time_mins=60):
        self.time_left = time_mins * 60
        self.status = 'running'
        self.is_running = True
        # Pobieramy wszystkich z rejestru
        for player in self.registry.get_all_players():
            self.sync_player(player)
            token = player.tag.generate_new_token()
            self.mqtt.send_command(player.tag.dev_eui, token, "START")

    def stop_round(self):
        self.status = 'stopped'
        self.is_running = False

    def reset_round(self):
        self.status = 'configuration'
        self.time_left = 0
        self.is_running = False

    """
        Autorejestracja nowego urządzenia, które wysyła uplink, ale nie jest w bazie tagów.
    """
    def auto_register_new_device(self, dev_eui):

        tag = DeviceTag(dev_eui)
        self.registry.register_tag(tag)
        return tag

    def create_active_players(self):
        for dev_eui, tag in self.registry._all_tags.items():
            profile = self.registry.get_profile_by_eui(dev_eui)
            if profile is None:
                continue  # tag bez profilu → pomiń

            player = ActivePlayer(
                device_tag=tag,
                profile=profile,
                team=profile.team  # jeśli profil ma team
            )
            self.registry.link_player(player)
            self.add_player(player)

    """
        Autorejestracja nowego gracza, który wysyła uplink, ale nie jest w bazie graczy.
        Tworzy tymczasowy profil gracza na podstawie taga, można później edytować w panelu admina.
    """

    def auto_register_new_profile(self, tag):
        profile = PlayerProfile(
            nickname=f"Player_{tag.dev_eui[-4:]}",
            role="Rekrut"
        )
        self.registry.register_profile(profile, tag.dev_eui)
        self.asg_app.profiles[profile.player_id] = profile
        self.asg_app.save_profiles()
        print(f"[AUTO] Utworzono profil {profile.nickname} dla taga {tag.dev_eui}")
        return profile

    def process_incoming_event(self, dev_eui, game_data, rssi, snr):
        # 1. Próba pobrania istniejącego gracza
        player = self.registry.get_player_by_eui(dev_eui)
        print(f"[DEBUG] Gracz znaleziony: {'TAK' if player else 'NIE'}")

        # 2. Obsługa braku gracza (Auto-rejestracja)
        if not player:
            print(f"[SESSION] Nieznane urządzenie {dev_eui}. Uruchamiam auto-rejestrację.")

            # Najpierw pobieramy/tworzymy sam TAG
            tag = self.auto_register_new_device(dev_eui)

            # GWARDIA: Sprawdzamy czy obiekt tag w ogóle powstał
            if tag is None:
                print(f"[ERROR] Nie udało się stworzyć/pobrać taga dla {dev_eui}")
                return

            # Tworzymy profil i gracza
            profile = self.auto_register_new_profile(tag)
            print(f"[DEBUG] Profil dla {dev_eui}: {profile.nickname} (ID: {profile.player_id})")

            player = ActivePlayer(device_tag=tag, profile=profile, team=0)
            print(f"[DEBUG] Stworzono ActivePlayer dla {dev_eui} | Profil: {player.profile.nickname}, Team: {player.team}")

            # Rejestrujemy gracza w sesji
            self.add_player(player)
            print(f"[DEBUG] Pomyślnie zarejestrowano auto-gracza dla {dev_eui}")

        # 3. OSTATECZNA WERYFIKACJA (Gwardia przed aktualizacją metryk)
        # Sprawdzamy czy player i player.tag istnieją przed kropką
        if not player or not hasattr(player, 'tag') or player.tag is None:
            print(f"[ERROR] Obiekt gracza lub taga dla {dev_eui} jest uszkodzony (NoneType)")
            return

        # 4. AKTUALIZACJA METRYK (Bezpieczna)
        try:
            player.tag.update_metrics(rssi, snr)
            player.tag.last_seen = time.time()
            player.tag.status = "ONLINE"  # To kluczowe dla frontendu
        except AttributeError as e:
            print(f"[ERROR] Błąd atrybutu status w obiekcie Tag: {e}")
            return

        # 5. OBSŁUGA TYPÓW WIADOMOŚCI
        msg_type = game_data.get("type")

        if msg_type == "TELEMETRY":
            # Używamy .get z domyślną wartością, aby nie wywalić się na braku klucza
            player.lat = game_data.get("lat", 0.0)
            player.lon = game_data.get("lon", 0.0)
            print(f"[GAME] Otrzymano TELEMETRY od {player.profile.nickname} | Lat: {player.lat}, Lon: {player.lon}")

        elif msg_type == "ACK_APP":
            token = game_data.get("token")
            print(f"[GAME] Otrzymano ACK_APP od {player.profile.nickname} | Token: {token}")
            if token is not None:
                player.tag.confirm_ack(token)

        elif msg_type == "EVENT":
            event_status = game_data.get("status")
            print(f"[GAME] Otrzymano EVENT od {player.profile.nickname} | Status: {event_status}")
            if event_status == "KILLED":
                if self.mode:
                    print(f"[GAME] Gracz {player.profile.nickname} został trafiony!")
                    self.mode.on_hit(player, self)

        elif msg_type == "PING":
            # Bezpieczne sprawdzenie synchronizacji
            is_synced = getattr(player.tag, 'is_synced', True)
            print(f"[GAME] Otrzymano PING od {player.profile.nickname} | Synced: {is_synced}")
            if not is_synced:
                print(f"[GAME] Autorepair: Synchronizacja dla {player.profile.nickname}")
                self.sync_player(player)

    def sync_player(self, player):
        if not player or not player.profile:
            return  # Nie synchronizuj graczy bez profilu
        
        token = player.tag.generate_new_token()

        self.mqtt.send_config(
            dev_eui=player.tag.dev_eui,
            token=token,
            team=player.team,
            game_type=1,  # ID trybu gry (można wyciągnąć z self.mode)
            time_mins=60,
            allies_tot=self._count_team(player.team),
            enemies_tot=self._count_team(1 - player.team),
            nickname=player.profile.nickname
        )
        player.tag.downlink_count += 1  # Zwiększamy licznik downlinków

    def broadcast_state(self):
        if not self.is_running: return
        for player in self.registry.get_all_players():
            update_data = self.mode.get_game_update_data(player, self)
            self.mqtt.send_update(player.tag.dev_eui, update_data["allies"], update_data["enemies"])

    """
        Zlicza graczy w danej drużynie
    """
    def _count_team(self, team_id):
        return sum(1 for p in self.registry.get_all_players() if p.team == team_id)