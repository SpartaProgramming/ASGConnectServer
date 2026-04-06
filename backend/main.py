import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) #wyszukiwanie modułów
import config
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.game_state import GameState
if config.USE_MOCK:
    from core.mqtt_handler import MockMQTTHandler as MQTTHandler
else:
    from core.mqtt_handler import MQTTHandler
import asyncio
from pydantic import BaseModel
from core.game_manager import GameManager


app = FastAPI()

# --- DODAJEMY CORS, ABY VUE MOGŁO GADAĆ Z PYTHONEM ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W wersji produkcyjnej podaje się tu konkretne IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = GameState()
mqtt = MQTTHandler(state)
game = GameManager(state)

# Struktura dla zapytania spoofowania
class SpoofRequest(BaseModel):
    dev_eui: str
    lat: float
    lon: float


@app.post("/api/game/start")
async def start_game(config: dict):
    # config: {"type": "CTF", "duration": 1800}
    game.setup_game(config.get("type"), config.get("duration"))
    asyncio.create_task(game.run_game_loop())
    return {"status": "started"}

@app.post("/api/game/assign")
async def assign_team(data: dict):
    # data: {"dev_eui": "ABC111", "team": "RED"}
    game.assign_to_team(data["dev_eui"], data["team"])
    return {"status": "assigned"}


# --- NOWY ENDPOINT API DO SPOOFOWANIA ---
@app.post("/api/spoof")
async def spoof_player(req: SpoofRequest):
    if req.dev_eui in state.players:
        # Wymuszamy nową pozycję bezpośrednio w State
        state.players[req.dev_eui].update({"lat": req.lat, "lon": req.lon})
        # Musimy powiadomić WebSockety, że State się zmienił!
        state.notify_callbacks(state.players)
        return {"status": "success", "message": f"Przesunięto {req.dev_eui}"}
    return {"status": "error", "message": "Player not found"}

# ... startup_event, websocket_endpoint ...

@app.on_event("startup")
def startup_event():
    mqtt.start()


@app.on_event("shutdown")
def shutdown_event():
    mqtt.stop()

# Otwiera dwukierunkowe połączenie z frontend.
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Pobieramy aktualną pętlę zdarzeń, żeby móc do niej "wrzucać" zadania z innego wątku
    loop = asyncio.get_running_loop()

    # Wysyłamy dane na start
    await websocket.send_json({"type": "UPDATE_PLAYERS", "data": state.players})

    def on_state_change(players_data):
        coro = websocket.send_json({"type": "UPDATE_PLAYERS", "data": players_data})
        asyncio.run_coroutine_threadsafe(coro, loop)

    state.callbacks.append(on_state_change)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "SEND_COMMAND":
                mqtt.send_command(data["dev_eui"], data["command"])
    except WebSocketDisconnect:
        print("Frontend się rozłączył")
    finally:
        # Bardzo ważne: usuwamy callback, żeby nie wysyłać danych do nieistniejącego okna!
        if on_state_change in state.callbacks:
            state.callbacks.remove(on_state_change)