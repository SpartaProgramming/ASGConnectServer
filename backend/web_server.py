from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from ASGConnect import ASGConnect  # Import klasy głównej
from ActivePlayer import ActivePlayer
import time
from fastapi import Request


app = FastAPI()

main_loop = None



# CORS dla frontendu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji ogranicz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancja aplikacji ASG
asg_app = ASGConnect()

# Lista połączonych WebSocket klientów
connected_clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"[WS] Nowy klient podłączony. Razem: {len(connected_clients)}")
    try:
        # Wyślij początkową aktualizację
        broadcast_update()
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
    except asyncio.TimeoutError:
        # Timeout, send ping
        try:
            await websocket.send_json({"type": "PING"})
        except:
            pass
    except Exception as e:
        print(f"[WS] WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"[WS] Klient odłączony. Razem: {len(connected_clients)}")

"""
    Buduje słownik JSON graczy, wysyła do połączonych WebSocketów, bez blokowannia wątku (wywołane z MQTT)
"""


def broadcast_update():
    players_data = {}

    # Pobieramy kopię tagów, aby uniknąć błędów iteracji
    all_tags = asg_app.registry.get_all_tags_safe()
    player_map = asg_app.registry.get_tag_to_player_map()

    print(f"[WS] Zebrano {len(all_tags)} tagów do przetworzenia.")

    for dev_eui, tag in all_tags.items():
        if tag is None:
            print(f"[WS] Ostrzeżenie: Tag {dev_eui} jest None, pomijam.")
            continue

        player = player_map.get(dev_eui)


        # Oblicz status połączenia na podstawie last_seen
        now = time.time()
        last_seen = getattr(tag, 'last_seen', 0)
        if now - last_seen < 60:  # < 1 min = ONLINE
            connection_status = "ONLINE"
        elif now - last_seen < 300:  # 1-5 min = TIMEOUT
            connection_status = "TIMEOUT"
        else:  # > 5 min = OFFLINE
            connection_status = "OFFLINE"

        # Budujemy dane techniczne (zawsze dostępne z taga)
        tag_info = {
            "status": connection_status,  # Status połączenia urządzenia
            "rssi": getattr(tag, 'rssi', -120),
            "uplink_count": getattr(tag, 'uplink_count', 0),
            "downlink_count": getattr(tag, 'downlink_count', 0),
            "last_seen": last_seen,
            "lat": 0.0,
            "lon": 0.0,
            "is_alive": False,
            "nickname": "NIEZNANY",
            "team": 0,
            "profile_id": None
        }

        # BEZPIECZNIK 2: Jeśli gracz istnieje, nadpisujemy dane profilowe
        if player is not None:
            p_status = getattr(player, 'status', 'ALIVE')
            tag_info.update({
                "is_alive": p_status == "ALIVE",
                "lat": getattr(player, 'lat', 0.0),
                "lon": getattr(player, 'lon', 0.0),
                "team": getattr(player, 'team', 0),
            })

            if player.profile:
                tag_info["nickname"] = getattr(player.profile, 'nickname', 'N/A')
                tag_info["profile_id"] = getattr(player.profile, 'player_id', None)

        players_data[dev_eui] = tag_info

    current_session = asg_app.session
    # Payload dla frontendu
    message = {
        "type": "UPDATE_PLAYERS",
        "data": players_data,
        "game_status": getattr(current_session, 'status', 'configuration'),
        "time_left": getattr(current_session, 'time_left', 0)
    }

    # Wysłanie przez WebSocket (z zachowaniem main_loop)
    if connected_clients:
        for client in connected_clients.copy():
            try:
                # Sprawdzamy tylko czy main_loop został już przypisany
                if main_loop:
                    asyncio.run_coroutine_threadsafe(client.send_json(message), main_loop)
            except Exception as e:
                print(f"[WS] Błąd wysyłki: {e}")
                pass

async def broadcast_loop():
    """Pętla wysyłająca aktualizacje co sekundę"""
    while True:
        await asyncio.sleep(1)
        if connected_clients:
            broadcast_update()

@app.post("/api/game/start")
async def start_game(data: dict = {}):
    time_mins = data.get("time_mins", 60)
    asg_app.session.start_round(time_mins=time_mins)
    broadcast_update()
    return {"status": "Game started"}

@app.post("/api/game/stop")
async def stop_game():
    asg_app.session.stop_round()
    broadcast_update()
    return {"status": "Game stopped"}

@app.post("/api/game/reset")
async def reset_game():
    asg_app.session.reset_round()
    asg_app.registry._tag_to_player = {}
    broadcast_update()
    return {"status": "Game reset"}

@app.post("/api/game/respawn/{dev_eui}")
async def respawn_player(dev_eui: str):
    player = asg_app.registry.get_player_by_eui(dev_eui.upper())
    if player:
        player.status = "ALIVE"
        token = player.tag.generate_new_token()
        asg_app.mqtt.send_command(dev_eui.upper(), token, "RESPAWN")
        broadcast_update()
        return {"status": f"Player {dev_eui} respawned"}
    return {"error": "Player not found"}

@app.post("/api/spoof")
async def spoof_gps(data: dict):
    dev_eui = data.get("dev_eui")
    lat = data.get("lat")
    lon = data.get("lon")
    player = asg_app.registry.get_player_by_eui(dev_eui.upper())
    if player:
        player.lat = lat
        player.lon = lon
        broadcast_update()
        return {"status": f"GPS spoofed for {dev_eui}"}
    return {"error": "Player not found"}

@app.get("/api/profiles")
async def get_profiles():
    return asg_app.get_profiles()

@app.post("/api/profiles")
async def add_profile(data: dict):
    nickname = data.get("nick")
    role = data.get("role", "Rekrut")
    if nickname:
        profile = asg_app.add_profile(nickname, role)
        return profile.to_dict()
    return {"error": "Nickname required"}


@app.put("/api/profiles/{profile_id}") #pobieranie stringa z URL i parsownaie JSON -> dict
async def edit_profile(profile_id: str, data: dict): #type hinting, jak sparsować
    nickname = data.get("nick")
    role = data.get("role")
    if asg_app.edit_profile(profile_id, nickname, role):
        return {"status": "Updated"}
    return {"error": "Profile not found"}

@app.delete("/api/profiles/{profile_id}") #path parameter
async def delete_profile(profile_id: str):
    if asg_app.delete_profile(profile_id):
        return {"status": "Deleted"}
    return {"error": "Profile not found"}


@app.post("/api/game/mode")
async def set_game_mode(request: Request):
    data = await request.json()
    mode_id = data.get("mode_id", "1")

    asg_app.prepare_game(mode_id)

    return {"status": "Mode set"}


"""
    Endpointy do przypisywania drużyny i profilu do ActivePalyer
"""
@app.put("/api/players/{dev_eui}/team")
async def assign_team(dev_eui: str, data: dict):
    team_id = data.get("team")
    player = asg_app.registry.get_player_by_eui(dev_eui.upper())
    if player:
        player.team = int(team_id)
        asg_app.session.sync_player(player)
        return {"status": "Team assigned"}
    return {"error": "Player not found"}

@app.put("/api/players/{dev_eui}/profile")
async def assign_profile(dev_eui: str, data: dict):
    profile_id = data.get("profile_id")
    dev_eui_upper = dev_eui.upper()
    player = asg_app.registry.get_player_by_eui(dev_eui_upper)
    tag = asg_app.registry.get_tag(dev_eui_upper)
    if not tag:
        return {"error": "Tag not found"}
    if player:
        if profile_id and profile_id in asg_app.profiles:
            player.profile = asg_app.profiles[profile_id]
        else:
            player.profile = None
    else:
        # Jeśli nie ma gracza, ale jest tag, utwórz nowego ActivePlayer z profilem
        if profile_id and profile_id in asg_app.profiles:
            profile = asg_app.profiles[profile_id]
            player = ActivePlayer(device_tag=tag, profile=profile, team=0)  # domyślna drużyna
            asg_app.session.add_player(player)
        else:
            return {"error": "Profile required to create player"}
    asg_app.session.sync_player(player)
    return {"status": "Profile assigned"}

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    print("[APP] Pętla asyncio przejęta.")

    # Uruchom broadcast loop
    asyncio.create_task(broadcast_loop())
    print("[APP] Broadcast loop uruchomiony")

    # Uruchom ASGConnect
    asg_app.start()
    print("[APP] Inicjalizacja ASGConnect...")

    # Uruchom serwer web
    print("[APP] Uruchamianie serwera webowego...")
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
