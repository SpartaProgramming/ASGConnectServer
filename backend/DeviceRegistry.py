from time import time

class DeviceRegistry:
    def __init__(self):
        # Słownik wszystkich urządzeń, które kiedykolwiek się zameldowały
        self._all_tags = {}  # {dev_eui: DeviceTag}
        # Słownik powiązań: który tag należy do którego gracza
        self._tag_to_player = {} # {dev_eui: ActivePlayer}
        self._profiles_by_eui = {}

    def register_tag(self, device_tag):
        self._all_tags[device_tag.dev_eui.upper()] = device_tag

    def get_all_tags_safe(self):
        """Zwraca bezpieczną kopię słownika tagów do odczytu."""
        return dict(self._all_tags)  # Tworzy nową kopię, odporną na zmiany w trakcie pętli

    def register_profile(self, profile, dev_eui):
        self._profiles_by_eui[dev_eui.upper()] = profile

    def get_profile_by_eui(self, dev_eui):
        return self._profiles_by_eui.get(dev_eui.upper())

    def link_player(self, active_player):
        dev_eui = active_player.tag.dev_eui.upper()
        self._tag_to_player[dev_eui] = active_player
        print(f"[REGISTRY] Połączono {dev_eui} z profilem {active_player.profile.nickname}")

    def get_player_by_eui(self, dev_eui):
        return self._tag_to_player.get(dev_eui.upper())

    def get_tag(self, dev_eui):
        return self._all_tags.get(dev_eui.upper())

    def get_all_offline_tags(self, timeout=300):
        now = time.time()
        return [tag for tag in self._all_tags.values() if now - tag.last_seen > timeout]

    def get_tag_to_player_map(self):
        """Zwraca kopię mapowania dla bezpiecznego odczytu w broadcast_update"""
        return dict(self._tag_to_player)

    """
    Metoda pomocnicza do pobierania wszystkich aktywnych graczy (np. do wyświetlania listy)
    """
    def get_all_players(self):
        return list(self._tag_to_player.values())