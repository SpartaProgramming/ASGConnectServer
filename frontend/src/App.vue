<template>
  <div class="command-center">
    <header class="top-bar">
      <h1>ASGConnect Tactical Suite</h1>
      <div class="clock-display">Lokalny czas: <strong>{{ currentTime }}</strong></div>
    </header>

    <div class="connection-status" :class="{ 'connected': isConnected }">
      Status serwera: {{ isConnected ? 'ONLINE' : 'OFFLINE' }}
    </div>

    <nav class="tabs">
      <button @click="activeTab = 'map'" :class="{ 'active': activeTab === 'map' }">Podgląd mapy</button>
      <button @click="activeTab = 'tags'" :class="{ 'active': activeTab === 'tags' }">Status jednostek</button>
      <button @click="activeTab = 'game'" :class="{ 'active': activeTab === 'game' }">Kontrola operacji</button>
    </nav>

    <main class="tab-content">

      <div v-if="activeTab === 'map'" class="tab-pane no-padding">
        <TacticalMap :players="players" :isActive="activeTab === 'map'" />
      </div>

      <div v-if="activeTab === 'tags'" class="tab-pane">
        <div class="tags-layout">
          <div class="tags-table-wrapper">
            <h2>Status Urządzeń w Terenie</h2>
            <table class="tactical-table">
              <thead>
              <tr>
                <th>ID (DevEUI)</th>
                <th>Status</th>
                <th>Sygnał</th>
                <th>Akcje</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="(data, devEui) in players" :key="devEui" :class="{ 'dead-row': !data.is_alive }">
                <td class="player-id">{{ devEui }}</td>
                <td>
                  <span :class="data.is_alive ? 'status-alive' : 'status-dead'">
                    {{ data.is_alive ? 'AKTYWNY' : 'WYELIMINOWANY' }}
                  </span>
                </td>
                <td>{{ data.rssi }} dBm</td>
                <td>
                  <button v-if="!data.is_alive" @click="respawnPlayer(devEui)" class="btn-respawn">WSKRZEŚ</button>
                  <button @click="startSpoofing(devEui, data.lat, data.lon)" class="btn-spoof">SPOOF</button>
                </td>
              </tr>
              <tr v-if="Object.keys(players).length === 0">
                <td colspan="4">Brak aktywnych jednostek...</td>
              </tr>
              </tbody>
            </table>
          </div>

          <div v-if="showSpoofPanel" class="admin-panel spoof-pane">
            <h2>GPS Spoofing</h2>
            <div class="spoof-form">
              <label>Urządzenie: <strong class="player-id">{{ spoofForm.dev_eui }}</strong></label>
              <div class="input-group">
                <input v-model.number="spoofForm.lat" type="number" step="0.0001" placeholder="Lat">
                <input v-model.number="spoofForm.lon" type="number" step="0.0001" placeholder="Lon">
              </div>
              <div class="action-group">
                <button @click="submitSpoof" class="btn-attack">WYŚLIJ POZYCJĘ</button>
                <button @click="cancelSpoof" class="btn-close">Anuluj</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'game'" class="tab-pane">
        <div class="game-management">

          <section class="admin-panel shadow">
            <h2>⚙️ Kontrola Systemu Walki</h2>
            <div class="setup-row main-controls">
              <div class="status-box" :class="{ 'active': gameStatus.is_running }">
                {{ gameStatus.is_running ? 'OPERACJA W TOKU' : 'SYSTEM WSTRZYMANY' }}
              </div>

              <div class="btn-group">
                <button v-if="!gameStatus.is_running" @click="startGame" class="btn-attack large">START MISJI</button>
                <button v-else @click="stopGame" class="btn-stop large">STOP (FREEZE)</button>
                <button @click="resetGame" class="btn-reset">RESET GLOBALNY</button>
              </div>
            </div>
          </section>

          <section class="admin-panel shadow mt-20">
            <h2>📊 Statystyki Deadmatch</h2>
            <div class="stats-grid">
              <div class="stat-card">
                <label>Aktywne jednostki</label>
                <div class="value">{{ aliveCount }}</div>
              </div>
              <div class="stat-card red">
                <label>Straty (KIA)</label>
                <div class="value">{{ deadCount }}</div>
              </div>
            </div>
          </section>

        </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import TacticalMap from './components/TacticalMap.vue'

// --- STAN APLIKACJI ---
const players = ref({})
const isConnected = ref(false)
const activeTab = ref('game')
const currentTime = ref('')
const gameStatus = ref({ is_running: false })

let socket = null
let clockInterval = null

// --- STAN SPOOFOWANIA ---
const showSpoofPanel = ref(false)
const spoofForm = ref({ dev_eui: '', lat: 0, lon: 0 })

// --- COMPUTED ---
const aliveCount = computed(() => Object.values(players.value).filter(p => p.is_alive).length)
const deadCount = computed(() => Object.values(players.value).filter(p => !p.is_alive).length)

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
}

// --- AKCJE API ---
const startGame = async () => {
  await fetch('http://127.0.0.1:8000/api/game/start', { method: 'POST' });
};

const stopGame = async () => {
  await fetch('http://127.0.0.1:8000/api/game/stop', { method: 'POST' });
};

const resetGame = async () => {
  if(confirm("Czy na pewno zresetować stan wszystkich jednostek?")) {
    await fetch('http://127.0.0.1:8000/api/game/reset', { method: 'POST' });
  }
};

const respawnPlayer = async (devEui) => {
  await fetch(`http://127.0.0.1:8000/api/game/respawn/${devEui}`, { method: 'POST' });
};

async function submitSpoof() {
  try {
    await fetch('http://127.0.0.1:8000/api/spoof', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spoofForm.value)
    })
    showSpoofPanel.value = false
  } catch (e) { console.error(e) }
}

// --- CYKL ŻYCIA ---
onMounted(() => {
  updateClock()
  clockInterval = setInterval(updateClock, 1000)

  socket = new WebSocket("ws://127.0.0.1:8000/ws")
  socket.onopen = () => isConnected.value = true
  socket.onclose = () => isConnected.value = false

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === "UPDATE_PLAYERS") {
      players.value = msg.data
    } else if (msg.type === "GAME_UPDATE") {
      gameStatus.value = msg.data
    }
  }
})

onUnmounted(() => {
  clearInterval(clockInterval)
  if (socket) socket.close()
})
</script>

<style scoped>
/* Motyw militarny */
.command-center { font-family: 'Consolas', monospace; background-color: #0a0a0a; color: #d0d0d0; min-height: 100vh; padding: 20px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #222; padding-bottom: 10px; }
h1 { color: #00ff00; text-transform: uppercase; letter-spacing: 2px; }

.connection-status { padding: 5px 15px; border-radius: 3px; font-size: 0.8rem; margin: 10px 0; display: inline-block; border: 1px solid #444; }
.connected { border-color: #00ff00; color: #00ff00; }

.tabs button { background: #1a1a1a; border: 1px solid #333; color: #777; padding: 12px 25px; cursor: pointer; transition: 0.2s; }
.tabs button.active { background: #222; color: #00ff00; border-bottom: 2px solid #00ff00; }

.tab-pane { background: #111; border: 1px solid #222; padding: 20px; min-height: 60vh; }
.tactical-table { width: 100%; border-collapse: collapse; }
.tactical-table th { background: #1a1a1a; color: #00ff00; padding: 15px; text-align: left; }
.tactical-table td { padding: 12px; border-bottom: 1px solid #222; }

/* Statusy graczy */
.status-alive { color: #00ff00; font-weight: bold; }
.status-dead { color: #ff0000; font-weight: bold; text-decoration: line-through; }
.dead-row { background: rgba(255, 0, 0, 0.05); }

/* Przyciski */
.btn-attack { background: #006400; color: white; border: none; padding: 10px 20px; cursor: pointer; }
.btn-stop { background: #8b0000; color: white; border: none; padding: 10px 20px; cursor: pointer; }
.btn-reset { background: #444; color: white; border: none; padding: 10px 20px; cursor: pointer; margin-left: 10px; }
.btn-respawn { background: #0044ff; color: white; border: none; padding: 5px 10px; cursor: pointer; margin-right: 5px; }
.btn-spoof { background: #6a1b9a; color: white; border: none; padding: 5px 10px; cursor: pointer; }

/* Dashboard gry */
.main-controls { display: flex; align-items: center; justify-content: space-between; background: #1a1a1a; padding: 30px; border-radius: 5px; }
.status-box { font-size: 1.5rem; font-weight: bold; color: #444; }
.status-box.active { color: #00ff00; text-shadow: 0 0 10px rgba(0,255,0,0.5); }
.stats-grid { display: flex; gap: 20px; margin-top: 20px; }
.stat-card { background: #1a1a1a; padding: 20px; flex: 1; border-radius: 5px; text-align: center; border: 1px solid #333; }
.stat-card.red { border-color: #8b0000; }
.stat-card .value { font-size: 3rem; font-weight: bold; margin-top: 10px; }

.mt-20 { margin-top: 20px; }
</style>