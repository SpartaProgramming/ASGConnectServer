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
import sqlite3
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from core.database import init_db, save_config_to_db

# Konfiguracja logowania (zrób to raz tutaj, zadziała globalnie)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("server_logs.log"), logging.StreamHandler()]
)

# Importujemy odpowiedniego Handlera zależnie od konfiguracji
if config.USE_MOCK:
    from core.mqtt_handler import MockMQTTHandler as MQTTHandler
else:
    from core.mqtt_handler import MQTTHandler


# Inicjalizacja bazy przy starcie
init_db()

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = GameState()
game = GameManager(state)
mqtt = MQTTHandler(state, game)

game.set_mqtt(mqtt)


red_team = Team("RED")
blue_team = Team("BLUE")
current_game = Deathmatch({"RED": red_team, "BLUE": blue_team})


class GameSetup(BaseModel):
    teams: dict
    type: str = "TDM"

@app.post("/api/game/setup")
async def setup_game(config: GameSetup):
    try:
        logging.info(f"⚙️ Otrzymano nową konfigurację: {config.type}")
        logging.info(f"🔴 RED: {config.teams.get('RED')}")
        logging.info(f"🔵 BLUE: {config.teams.get('BLUE')}")

        # 1. Zapis do bazy danych (SQLite)
        save_config_to_db(config.type, config.teams)
        logging.info("💾 Konfiguracja zapisana w bazie game_history.db")

        # 2. Inicjalizacja Twojej klasy logiki (np. Deathmatch)
        # Zakładając, że masz funkcję pomocniczą do budowania obiektów Team
        teams_objects = {}
        for team_name, members in config.teams.items():
            # Tutaj tworzysz obiekty Team z Twojej klasy
            # teams_objects[team_name] = Team(name=team_name, members=members)
            pass

        # game_manager.current_match = Deathmatch(teams_objects)

        return {"status": "success", "message": "Konfiguracja załadowana i zapisana."}

    except Exception as e:
        logging.error(f"❌ Błąd podczas setupu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/game/respawn/{dev_eui}")
async def respawn_player(dev_eui: str):
    if dev_eui not in state.players:
        return {"status": "error", "message": "Nie znaleziono gracza"}

    game.respawn_player(dev_eui)
    return {"status": "success", "message": f"Wskrzeszono gracza {dev_eui}"}


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