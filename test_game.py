from backend.core.game_manager import GameManager

# 1. Tworzymy główny zarząd
gm = GameManager()

# 2. Wykrywamy urządzenia na poligonie (sygnał LoRa na start)
print("--- LOGOWANIE URZĄDZEŃ ---")
urzadzenia = ["ID_001", "ID_002", "ID_003", "ID_004"]
for u in urzadzenia:
    gm.register_device(u)
print(f"Wykryto {len(gm.players_pool)} urządzeń.")

# 3. Dowódca dzieli na drużyny
print("\n--- PRZYDZIAŁ DO DRUŻYN ---")
gm.assign_to_team("ID_001", "RED")
gm.assign_to_team("ID_002", "RED")
gm.assign_to_team("ID_003", "BLUE")
gm.assign_to_team("ID_004", "BLUE")

print(f"Czerwoni: {gm.teams['RED'].total_count} graczy")
print(f"Niebiescy: {gm.teams['BLUE'].total_count} graczy")

# 4. Startujemy grę
print("\n--- START GRY ---")
gm.start_game("Deathmatch")

# 5. Symulacja strzałów
print("\n[Walka] ID_001 (RED) dostaje...")
gm.report_hit("ID_001")
print("Status:", gm.active_mode.get_stats())

print("\n[Walka] ID_002 (RED) dostaje...")
gm.report_hit("ID_002")
# Gra powinna automatycznie ogłosić zwycięstwo NIEBIESKICH w terminalu!

print("\nStatus końcowy:", gm.active_mode.get_stats())