# Dokumentacja Architektury ASGConnectServerVUE

## Wstęp
ASGConnectServerVUE to system zarządzania grami airsoft w czasie rzeczywistym, wykorzystujący urządzenia LoRaWAN. Backend napisany w Pythonie obsługuje komunikację MQTT z serwerem ChirpStack, zarządza sesjami gry i automatycznie rejestruje graczy. Frontend w Vue.js zapewnia taktyczny dashboard dla sędziów z mapami na żywo, zarządzaniem drużynami i kontrolą gry.

## Struktura Katalogów
```
ASGConnectServerVUE/
├── backend/                          # Kod backendu w Pythonie
│   ├── main.py                       # Punkt wejścia aplikacji
│   ├── ASGConnect.py                 # Główna klasa aplikacji
│   ├── web_server.py                # Serwer FastAPI
│   ├── GameSession.py                # Zarządzanie sesjami gry
│   ├── MQTTHandler.py                # Obsługa MQTT
│   ├── DeviceRegistry.py             # Rejestr urządzeń
│   ├── ActivePlayer.py               # Model aktywnego gracza
│   ├── PlayerProfile.py              # Profil gracza
│   ├── DeviceTag.py                  # Model urządzenia LoRaWAN
│   ├── GameMode.py                   # Tryby gry
│   ├── database.py                   # Obsługa bazy danych SQLite
│   ├── config.py                     # Konfiguracja MQTT
│   └── __pycache__/                  # Cache Pythona
├── frontend/                         # Kod frontendu w Vue.js
│   ├── src/
│   │   ├── App.vue                   # Główny komponent aplikacji
│   │   ├── components/
│   │   │   └── TacticalMap.vue       # Komponent mapy taktycznej
│   │   ├── main.js                   # Punkt wejścia Vue
│   │   └── style.css                 # Style globalne
│   ├── package.json                  # Zależności Node.js
│   ├── vite.config.js                # Konfiguracja Vite
│   └── index.html                    # Główny plik HTML
├── game_history.db                   # Baza danych SQLite
├── server_logs.log                   # Logi serwera
└── AGENTS.md                         # Dokumentacja dla AI
```

## Architektura Ogólna
Aplikacja składa się z trzech głównych warstw:
- **Backend (Python)**: Obsługuje logikę gry, komunikację MQTT i zarządzanie danymi.
- **Frontend (Vue.js)**: Interfejs użytkownika dla sędziów, wyświetlający mapy, statusy i kontrolki gry.
- **Komunikacja**: MQTT dla urządzeń LoRaWAN; WebSocket i REST API dla frontendu (API nie zaimplementowane w kodzie backendu).

Zewnętrzne zależności:
- **ChirpStack**: Serwer LoRaWAN do obsługi urządzeń.
- **Mosquitto**: Broker MQTT.
- **Leaflet**: Biblioteka map dla frontendu.

## Główne Moduły
1. **Zarządzanie Grą (GameSession, GameMode)**: Obsługuje logikę gry, przetwarzanie zdarzeń i synchronizację urządzeń.
2. **Komunikacja MQTT (MQTTHandler)**: Wysyła i odbiera wiadomości MQTT z ChirpStack (tylko komunikacja).
3. **Rejestr Urządzeń (DeviceRegistry)**: Łączy DevEUI z obiektami graczy.
4. **Modele Danych (ActivePlayer, PlayerProfile, DeviceTag)**: Reprezentują graczy i urządzenia.
5. **Baza Danych (database.py)**: Przechowuje konfiguracje meczów i logi trafień.
6. **Frontend (App.vue, TacticalMap.vue)**: Wyświetla dashboard i mapę.
7. **Wybór Trybu Gry (GameModeFactory)**: Fabryka do wyboru trybów gry (Team Deathmatch, itp.).

## Przepływy Danych
1. **Uplink z Urządzenia**: MQTT topic `application/+/device/+/event/up` → MQTTHandler → GameSession.process_incoming_event() → przetwarzanie (telemetria, ACK, hit) → ewentualne downlinki.
2. **Downlink do Urządzenia**: GameSession → MQTTHandler.send_config/send_command/send_update → MQTT topic `application/{app_id}/device/{dev_eui}/command/down`.
3. **Frontend do Backendu**: WebSocket `ws://127.0.0.1:8000/ws` dla aktualizacji; REST API `http://127.0.0.1:8000/api/...` dla komend (nie zaimplementowane).
4. **Synchronizacja**: Tokeny dla potwierdzeń ACK; auto-rejestracja nowych urządzeń.
5. **Baza Danych**: Zapisywanie konfiguracji meczów i trafień do SQLite.

## Zależności
- **Python**: paho-mqtt (MQTT), sqlite3 (baza danych).
- **Node.js/Vue**: vue (framework), leaflet (mapy), vite (bundler).
- **Zewnętrzne**: Mosquitto (broker MQTT), ChirpStack (LoRaWAN server).

## Kluczowe Pliki
- `backend/main.py`: Punkt wejścia aplikacji, przekierowuje do web_server.py.
- `backend/ASGConnect.py`: Główna klasa aplikacji ASGConnect.
- `backend/web_server.py`: Serwer FastAPI z API REST i WebSocket dla frontendu.
- `backend/GameSession.py`: Przetwarzanie zdarzeń, zarządzanie graczami, synchronizacja.
- `backend/MQTTHandler.py`: Połączenie z brokerem, wysyłanie/receiving MQTT.
- `backend/DeviceRegistry.py`: Mapowanie DevEUI na graczy.
- `backend/database.py`: Funkcje dla SQLite.
- `frontend/src/App.vue`: Dashboard z zakładkami, WebSocket, API calls.
- `frontend/src/components/TacticalMap.vue`: Mapa Leaflet z pozycjami graczy.

## Najważniejsze Klasy
- **ASGConnect** (ASGConnect.py): Główna klasa aplikacji, koordynuje komponenty.
- **GameModeFactory** (ASGConnect.py): Fabryka do wyboru trybów gry.
- **GameSession** (GameSession.py): Zarządza sesją gry, przetwarza zdarzenia.
- **MQTTHandler** (MQTTHandler.py): Obsługuje tylko komunikację MQTT.
- **DeviceRegistry** (DeviceRegistry.py): Rejestr urządzeń.
- **ActivePlayer** (ActivePlayer.py): Łączy profil, tag i drużynę.
- **PlayerProfile** (PlayerProfile.py): Dane gracza (nick, rank, stats).
- **DeviceTag** (DeviceTag.py): Stan urządzenia (RSSI, sync, tokeny).
- **GameMode** (GameMode.py): Bazowa klasa trybów gry; TeamDeathmatch implementuje logikę trafień.

## Serwisy i Endpointy
Backend ma zaimplementowany serwer webowy w `web_server.py` z FastAPI:
- **WebSocket**: `ws://127.0.0.1:8000/ws` – aktualizacje graczy i statusu gry.
- **REST API**:
  - `POST /api/game/start` – start gry.
  - `POST /api/game/stop` – stop gry.
  - `POST /api/game/reset` – reset.
  - `POST /api/game/respawn/{dev_eui}` – wskrzeszenie gracza.
  - `POST /api/spoof` – spoof GPS.

## Sposób Uruchamiania Projektu
1. **Uruchom Web Server**: `cd backend && python web_server.py` (uruchamia MQTT i serwer webowy z API/WebSocket).
2. **Uruchom Frontend**: `cd frontend && npm install && npm run dev` (serwer na localhost:5173).
3. **Baza Danych**: Inicjalizuje się automatycznie przy pierwszym uruchomieniu.

## Sposób Działania Aplikacji
1. **Inicjalizacja**: Backend łączy się z MQTT, frontend otwiera WebSocket.
2. **Rejestracja**: Nowe urządzenie wysyła uplink → auto-rejestracja gracza, przypisanie drużyny.
3. **Gra**: Przetwarzanie telemetrii (GPS), zdarzeń (trafienia), ACK. Wysyłanie konfiguracji, komend (START, DIE), aktualizacji (żywi sojusznicy/wrogowie).
4. **Kontrola**: Sędzia używa menu backendu lub frontendu do start/stop/reset, przypisywania drużyn, spoofowania GPS.
5. **Wyświetlanie**: Frontend pokazuje mapę z pozycjami, statusami graczy, statystykami drużyn.
6. **Logowanie**: Wydruki w konsoli, zapisy do SQLite dla historii.
