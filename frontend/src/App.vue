<template>
  <div class="command-center">
    <header class="top-bar">
      <h1>ASGConnect</h1>
      <div class="clock-display">Lokalny czas: <strong>{{ currentTime }}</strong></div>
    </header>

    <div class="connection-status" :class="{ 'connected': isConnected }">
      Status serwera: {{ isConnected ? 'ONLINE' : 'OFFLINE' }}
    </div>

    <nav class="tabs">
      <button @click="activeTab = 'map'" :class="{ 'active': activeTab === 'map' }">Podgląd mapy</button>
      <button @click="activeTab = 'tags'" :class="{ 'active': activeTab === 'tags' }">Podłączone TAGI</button>
      <button @click="activeTab = 'game'" :class="{ 'active': activeTab === 'game' }">Konfiguracja rozgrywki</button>
    </nav>

    <main class="tab-content">

      <div v-if="activeTab === 'map'" class="tab-pane no-padding">
        <h2>Mapa Taktyczna</h2>
        <TacticalMap :players="players" :isActive="activeTab === 'map'" />
      </div>

      <div v-if="activeTab === 'tags'" class="tab-pane">
        <div class="tags-layout">
          <div class="tags-table-wrapper">
            <h2>Status Urządzeń</h2>
            <table class="tactical-table">
              <thead><tr><th>ID (DevEUI)</th><th>GPS</th><th>Sygnał</th><th>Rozkazy</th></tr></thead>
              <tbody>
              <tr v-for="(data, devEui) in players" :key="devEui">
                <td class="player-id">{{ devEui }}</td>
                <td>{{ data.lat.toFixed(5) }}, {{ data.lon.toFixed(5) }}</td>
                <td>{{ data.rssi }} dBm</td>
                <td>
                  <button @click="startSpoofing(devEui, data.lat, data.lon)" class="btn-spoof">SPOOF</button>
                </td>
              </tr>
              <tr v-if="Object.keys(players).length === 0"><td colspan="4">Czekam na sygnał...</td></tr>
              </tbody>
            </table>
          </div>

          <div v-if="showSpoofPanel" class="admin-panel spoof-pane">
            <h2>Panel Administratora (Spoofing)</h2>
            <div class="spoof-form">
              <label>Spoofowanie gracza: <strong class="player-id">{{ spoofForm.dev_eui }}</strong></label>
              <div class="input-group">
                <input v-model.number="spoofForm.lat" type="number" step="0.0001" placeholder="Latitude">
                <input v-model.number="spoofForm.lon" type="number" step="0.0001" placeholder="Longitude">
              </div>
              <p class="help-text">Mock generuje losowy "szum", ale ta pozycja jest bazą.</p>
              <div class="action-group">
                <button @click="submitSpoof" class="btn-retreat">SPOOFNIJ POZYCJĘ!</button>
                <button @click="cancelSpoof" class="btn-close">Anuluj</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'game'" class="tab-pane">
        <div class="game-management">

          <section class="admin-panel shadow">
            <h2>⚙️ Konfiguracja Operacji</h2>
            <div class="setup-row">
              <select v-model="gameConfig.type">
                <option value="CTF">Capture The Flag</option>
                <option value="TDM">Team Deathmatch</option>
                <option value="DOM">Dominacja</option>
              </select>
              <input type="number" v-model="gameConfig.duration" placeholder="Czas (minuty)">
              <button @click="startGame" class="btn-attack">ROZPOCZNIJ MISJĘ</button>
            </div>
          </section>

          <div class="game-status-grid">
            <div class="team-card red">
              <h3>🔴 Drużyna CZERWONI</h3>
              <div class="score">{{ gameStatus.scores.RED }}</div>
              <ul>
                <li v-for="id in gameStatus.teams.RED" :key="id">{{ id }}</li>
              </ul>
            </div>

            <div class="timer-card">
              <h3>CZAS DO KOŃCA</h3>
              <div class="big-timer">{{ formatTime(gameStatus.remaining_time) }}</div>
              <p>Tryb: {{ gameStatus.game_type }}</p>
            </div>

            <div class="team-card blue">
              <h3>🔵 Drużyna NIEBIESCY</h3>
              <div class="score">{{ gameStatus.scores.BLUE }}</div>
              <ul>
                <li v-for="id in gameStatus.teams.BLUE" :key="id">{{ id }}</li>
              </ul>
            </div>
          </div>

          <section class="admin-panel shadow">
            <h2>👥 Przydział jednostek</h2>
            <table class="tactical-table">
              <tr v-for="(data, id) in players" :key="id">
                <td>{{ id }}</td>
                <td>
                  <button @click="assignTeam(id, 'RED')" class="btn-red">Do Czerwonych</button>
                  <button @click="assignTeam(id, 'BLUE')" class="btn-blue">Do Niebieskich</button>
                </td>
              </tr>
            </table>
          </section>

        </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import TacticalMap from './components/TacticalMap.vue'

// --- STAN GRY ---
const gameConfig = ref({ type: 'CTF', duration: 30 })
const gameStatus = ref({
  is_running: false,
  remaining_time: 0,
  scores: { RED: 0, BLUE: 0 },
  teams: { RED: [], BLUE: [] },
  game_type: 'BRAK'
})

// --- STAN APLIKACJI ---
const players = ref({})
const isConnected = ref(false)
const activeTab = ref('tags')
const currentTime = ref('')
let socket = null
let clockInterval = null

// --- STAN SPOOFOWANIA ---
const showSpoofPanel = ref(false)
const spoofForm = ref({ dev_eui: '', lat: 0, lon: 0 })

// --- FUNKCJE POMOCNICZE ---
function updateClock() {
  currentTime.value = new Date().toLocaleTimeString('pl-PL')
}

function startSpoofing(devEui, lat, lon) {
  showSpoofPanel.value = true
  spoofForm.value = { dev_eui: devEui, lat, lon }
}

function cancelSpoof() {
  showSpoofPanel.value = false
  spoofForm.value = { dev_eui: '', lat: 0, lon: 0 }
}

function formatTime(seconds) {
  if (!seconds) return "00:00"
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// --- AKCJE API ---
async function submitSpoof() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/spoof', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spoofForm.value)
    })
    const result = await response.json()
    if (result.status === 'success') {
      alert(`Sukces!`); cancelSpoof()
    }
  } catch (e) { console.error(e) }
}

async function startGame() {
  await fetch('http://127.0.0.1:8000/api/game/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: gameConfig.value.type,
      duration: gameConfig.value.duration * 60
    })
  })
}

async function assignTeam(devEui, team) {
  await fetch('http://127.0.0.1:8000/api/game/assign', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dev_eui: devEui, team: team })
  })
}

// --- CYKL ŻYCIA ---
onMounted(() => {
  updateClock()
  clockInterval = setInterval(updateClock, 1000)

  socket = new WebSocket("ws://127.0.0.1:8000/ws")

  socket.onopen = () => {
    isConnected.value = true
  }

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data)

    // Obsługa różnych typów wiadomości w jednym miejscu
    if (msg.type === "UPDATE_PLAYERS") {
      players.value = msg.data
    } else if (msg.type === "GAME_UPDATE") {
      gameStatus.value = msg.data
    }
  }

  socket.onclose = () => {
    isConnected.value = false
  }
})

onUnmounted(() => {
  clearInterval(clockInterval)
  if (socket) socket.close()
})
</script>

<style>
/* GŁÓWNY UKŁAD I TAKTYCZNY MOTYW (Ciemny i wojskowy) */
.command-center { font-family: 'Courier New', Courier, monospace; background-color: #0d0d0d; color: #e0e0e0; min-height: 100vh; padding: 20px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 15px; }
h1 { color: #4CAF50; margin: 0; }
.clock-display { font-size: 1.2rem; background: #1a1a1a; padding: 10px 20px; border-radius: 5px; border: 1px solid #333; }
.connection-status { padding: 8px 15px; background-color: #420000; color: #ff5252; font-weight: bold; border-radius: 4px; margin-bottom: 20px; display: inline-block; }
.connection-status.connected { background-color: #003300; color: #4CAF50; }

/* ZAKŁADKI (TABS) */
.tabs { display: flex; gap: 10px; margin-bottom: 20px; }
.tabs button { background-color: #1a1a1a; color: #888; border: 1px solid #333; padding: 10px 20px; font-size: 1rem; cursor: pointer; border-radius: 4px 4px 0 0; font-family: inherit; transition: 0.3s; }
.tabs button.active { background-color: #1a1a1a; color: #4CAF50; border-bottom: 2px solid #4CAF50; font-weight: bold; }

/* ZAWARTOŚĆ ZAKŁADEK */
.tab-pane { background-color: #1a1a1a; padding: 20px; border: 1px solid #333; border-radius: 0 4px 4px 4px; }
.tab-pane.no-padding { padding: 0; }
.tab-pane h2 { color: #ccc; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 0; }

/* UKŁAD DLA ZAKŁADKI TAGI */
.tags-layout { display: flex; gap: 20px; }
.tags-table-wrapper { flex: 2; }
.admin-panel { flex: 1; border-left: 1px solid #333; padding-left: 20px; }

/* TABELA GRACZY */
.tactical-table { width: 100%; border-collapse: collapse; }
.tactical-table th, .tactical-table td { border: 1px solid #333; padding: 12px; text-align: left; }
.tactical-table th { background-color: #222; color: #4CAF50; }
.player-id { font-weight: bold; color: #fff; }

/* PRZYCISKI AKCJI */
button.btn-spoof, button.btn-retreat, button.btn-close {
  padding: 6px 12px; margin-right: 5px; border: none; cursor: pointer; font-weight: bold; border-radius: 3px; font-family: inherit;
}
.btn-spoof { background-color: #6a1b9a; color: white; } /* Fioletowy dla wyróżnienia Spoofowania */
.btn-retreat { background-color: #ffb300; color: black; }
.btn-close { background-color: #333; color: white; }

/* FORMULARZ SPOOFOWANIA */
.spoof-form { display: flex; flex-direction: column; gap: 15px; background-color: #222; padding: 20px; border-radius: 5px; }
.input-group { display: flex; gap: 10px; }
.input-group input { background-color: #0d0d0d; border: 1px solid #444; color: #e0e0e0; padding: 10px; border-radius: 4px; width: 100%; font-family: inherit;}
.help-text { font-size: 0.8rem; color: #888; margin: 0; font-style: italic; }
.action-group { display: flex; gap: 10px; }
</style>