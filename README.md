# Szybki Start

## Docker Compose (REKOMENDOWANE)

Uruchom wszystko jednoczesnie:
```bash
docker-compose up --build
```

Lub w tle:
```bash
docker-compose up -d
```

**Dostęp:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## Lokalnie (bez Docker)

### Terminal 1 - Backend + Web Server
```bash
cd backend
pip install -r requirements.txt
python web_server.py  # Główny punkt wejścia - uruchamia wszystko
```

### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm run dev
```

## Problemy z WebSocket

Jeśli widzisz błędy WebSocket:
1. Sprawdź czy backend działa: `curl http://localhost:8000`
2. Sprawdź konsolę przeglądarki (F12 → Console) szukaj `[WS]` logów
3. Upewnij się że broker ChirpStack jest dostępny (10.0.0.5:1883)

Pełne instrukcje: zobacz `DOCKER_README.md`
