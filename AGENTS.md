# AGENTS.md - AI Coding Assistant Guidelines for ASGConnectServerVUE

## Project Overview
ASGConnectServerVUE is a real-time airsoft game management system using LoRaWAN devices. The backend (Python) handles MQTT communication with ChirpStack, manages game sessions, and auto-registers players. The frontend (Vue.js) provides a tactical dashboard for referees with live maps, team management, and game control.

## Architecture
- **Backend**: Python classes for game logic (GameSession, GameMode), MQTT handling (MQTTHandler), device registry (DeviceRegistry), and data models (ActivePlayer, DeviceTag, PlayerProfile).
- **Frontend**: Vue 3 app with WebSocket for real-time updates and REST API for commands.
- **Communication**: MQTT via ChirpStack for device uplinks/downlinks; WebSocket/HTTP assumed for frontend-backend (backend code lacks web server implementation).
- **Database**: SQLite for match configs and hit logs.
- **External**: LoRaWAN via ChirpStack broker; Leaflet for maps.

## Key Components
- `backend/main.py`: Entry point with ASGConnect class, MQTT start, and referee menu.
- `backend/ASGConnect.py`: Główna klasa aplikacji ASGConnect z wyborem trybu gry.
- `backend/GameModeFactory.py`: Factory for selecting game modes (Team Deathmatch, etc.).
- `backend/web_server.py`: FastAPI server with REST API and WebSocket for frontend.
- `backend/GameSession.py`: Manages players, processes events (telemetry, ACK, hits), syncs devices.
- `backend/MQTTHandler.py`: Handles MQTT communication only (uplinks/downlinks).
- `backend/DeviceRegistry.py`: Links DevEUIs to ActivePlayer objects.
- `frontend/src/App.vue`: Main dashboard with tabs for map, tags, teams, game status.
- `frontend/src/components/TacticalMap.vue`: Leaflet-based map for player positions.

## Critical Workflows
- **Run Backend**: `cd backend && python main.py` (redirects to web_server.py).
- **Run Web Server**: `cd backend && python web_server.py` (starts MQTT, backend, and web API/WebSocket for frontend).
- **Run Frontend**: `cd frontend && npm install && npm run dev` (serves on localhost:5173).
- **Database Init**: Automatic via `backend/database.py` on first run.

## Project-Specific Patterns
- **MQTT Topics**: Uplink `application/+/device/+/event/up`; Downlink `application/{app_id}/device/{dev_eui}/command/down`.
- **Payloads**: JSON with `rxInfo` (RSSI/SNR), `object` (game data like lat/lon, type: TELEMETRY/EVENT/ACK/PING).
- **Device Sync**: Token-based acknowledgments; `pending_token` increments on commands, confirmed via ACK.
- **Auto-Registration**: New DevEUI on uplink creates PlayerProfile/DeviceTag/ActivePlayer, assigns team alternately.
- **Game Modes**: Base `GameMode` class; `TeamDeathmatch` marks hit players as DEAD, sends DIE command.
- **Frontend API**: Fetches to `http://127.0.0.1:8000/api/...` (start/stop/reset game, respawn, spoof GPS); WebSocket `ws://127.0.0.1:8000/ws` for updates.
- **Team Assignment**: RED (team 0), BLUE (team 1); updates broadcast allies/enemies alive counts.
- **Logging**: Print statements for events; SQLite for persistent history.

## Conventions
- **Naming**: DevEUI in uppercase; classes like GameSession, ActivePlayer.
- **Imports**: Relative in backend (e.g., `from mqtt_handler import MQTTHandler`).
- **Error Handling**: Basic try/except in MQTT; no extensive validation.
- **State Management**: Reactive in Vue (ref, computed); dicts in Python.
- **Styling**: Military theme in frontend (dark, green accents).

## Common Tasks
- Add new game mode: Extend `GameMode`, implement `on_hit`, `get_game_update_data`.
- Handle new event type: In `GameSession.process_incoming_event`, add case for `msg_type`.
- Update frontend: Modify `App.vue` tabs or add components; ensure WebSocket updates players/gameStatus.
