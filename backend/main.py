import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.game_state import GameState
from core.game_manager import GameManager
from core.models import Player, Team
from core.game_modes import Deathmatch
import asyncio
from pydantic import BaseModel

# Importujemy odpowiedniego Handlera zależnie od konfiguracji
if config.USE_MOCK:
    from core.mqtt_handler import MockMQTTHandler as MQTTHandler
else:
    from core.mqtt_handler import MQTTHandler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# POPRAWIONA INICJALIZACJA SYSTEMU
# ==========================================
state = GameState()
game = GameManager(state)
mqtt = MQTTHandler(state, game)

# TUTAJ JEST KLUCZ: Dajemy game managerowi dostęp do radia!
game.set_mqtt(mqtt)

# (Opcjonalnie) Przykładowa inicjalizacja drużyn
red_team = Team("RED")
blue_team = Team("BLUE")
current_game = Deathmatch({"RED": red_team, "BLUE": blue_team})


class SpoofRequest(BaseModel):
    dev_eui: str
    lat: float
    lon: float


@app.on_event("startup")
def startup_event():
    mqtt.start()

@app.on_event("shutdown")
def shutdown_event():
    mqtt.stop()


@app.post("/api/game/start")
async def start_game():
    game.start_game()
    return {"status": "success", "message": "Gra wystartowała. Tagi odblokowane."}


@app.post("/api/game/stop")
async def stop_game():
    game.stop_game()
    return {"status": "success", "message": "Gra zatrzymana. Tagi zablokowane."}


@app.post("/api/game/reset")
async def reset_game():
    game.reset_game()
    return {"status": "success", "message": "Zresetowano stan gry."}


# Endpoint dla przycisku "Wskrześ" w panelu Vue
@app.post("/api/game/respawn/{dev_eui}")
async def respawn_player(dev_eui: str):
    if dev_eui not in state.players:
        return {"status": "error", "message": "Nie znaleziono gracza"}

    game.respawn_player(dev_eui)
    return {"status": "success", "message": f"Wskrzeszono gracza {dev_eui}"}

@app.post("/api/game/assign")
async def assign_team(data: dict):
    game.assign_to_team(data["dev_eui"], data["team"])
    return {"status": "assigned"}

@app.post("/api/spoof")
async def spoof_player(req: SpoofRequest):
    if req.dev_eui in state.players:
        state.players[req.dev_eui].update({"lat": req.lat, "lon": req.lon})
        state.notify_callbacks(state.players)
        return {"status": "success", "message": f"Przesunięto {req.dev_eui}"}
    return {"status": "error", "message": "Player not found"}

@app.get("/api/players")
async def get_players():
    return state.players

@app.get("/api/game/status")
async def get_game_status():
    return {
        "is_running": game.is_running,
        "remaining_time": game.duration,
        "teams": game.teams,
        "scores": game.scores,
        "mode": game.game_type
    }

# ==========================================
# WEBSOCKET - Wysyłanie danych do VUE
# ==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()

    # Od razu po podłączeniu wysyłamy frontendowi obecnych graczy
    await websocket.send_json({"type": "UPDATE_PLAYERS", "data": state.players})

    def on_state_change(players_data):
        coro = websocket.send_json({"type": "UPDATE_PLAYERS", "data": players_data})
        asyncio.run_coroutine_threadsafe(coro, loop)

    # Rejestrujemy okno przeglądarki, żeby otrzymywało powiadomienia
    state.callbacks.append(on_state_change)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "SEND_COMMAND":
                mqtt.send_command(data["dev_eui"], data["command"])
    except WebSocketDisconnect:
        print("Frontend się rozłączył")
    finally:
        if on_state_change in state.callbacks:
            state.callbacks.remove(on_state_change)