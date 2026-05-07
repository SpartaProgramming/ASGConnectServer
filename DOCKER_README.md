# ASGConnectServerVUE - Quick Start Guide

## Połączenie RPI (Chirpstack z stacją roboczą)
- Kabel Ethernet: RPI <-> Stacja robocza
- RPI IP: static: 10.42.0.162
- Włączyć tryb Shared Network (Windows) lub udostępnić połączenie (Linux/Mac)

## Wymagania
- Python 3.10+ 
- Node.js 22+ 

## Uruchamianie z Docker Compose (Rekomendowane)

### 1. Zbuduj i uruchom kontenery
```bash
cd /home/sparta/PycharmProjects/ASGConnectServerVUE
docker-compose up --build
```

Lub w tle:
```bash
docker-compose up -d
```

### 2. Czekaj na start wszystkich serwisów
```
✓ Backend (http://10.42.0.1:8000)
✓ Frontend (http://10.42.0.1:5173)
```


### 3. Otwórz frontend
Przejdź do: **http://10.42.0.1:5173/** w przeglądarce

### 4. Zatrzymaj kontenery
```bash
docker-compose down
```

## Uruchamianie lokalnie (bez Docker)

### Backend
```bash
cd backend
pip install -r requirements.txt
python web_server.py
```

### Frontend (w osobnym terminalu)
```bash
cd frontend
npm install
npm run dev
```

## Struktura Docker

- **Backend**: Python FastAPI na porcie 8000
  - Obsługuje MQTT z ChirpStack (rzeczywisty broker)
  - WebSocket i REST API
  
- **Frontend**: Vue 3 + Vite na porcie 5173
  - Hot reload w dev mode
  - Łączy się z backend na ws://localhost:8000

## Troubleshooting

### Backend się nie łączy z MQTT
Edytuj `backend/config.py` i zmień IP brokera:
```python
BROKER_IP = "10.42.0.162"  # Zmień na IP Twojego brokera ChirpStack
```

### Usuwanie kontenerów
```bash
docker-compose down --volumes  # Usuń też volumy
docker system prune -a        # Wyczyść wszystko
```

## Pliki Konfiguracji

- `docker-compose.yml` - Orchestracja kontenerów
- `Dockerfile.backend` - Build backend kontenera
- `Dockerfile.frontend` - Build frontend kontenera

## Porty

| Serwis | Port | URL |
|--------|------|-----|
| Backend API | 8000 | http://localhost:8000 |
| Frontend | 5173 | http://localhost:5173 |

## Kontakt
- Email: michal.zawa123@gmail.com

