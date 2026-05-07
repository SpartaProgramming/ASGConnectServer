<template>
  <div class="command-center">
    <header class="top-bar">
      <h1>ASGConnect</h1>
      <div class="clock-display">Lokalny czas: <strong>{{ currentTime }}</strong></div>
    </header>

    <div class="connection-status" :class="{ 'connected': isConnected }">
      Status serwera: {{ isConnected ? 'ONLINE' : 'OFFLINE' }}
    </div>
    <div class="game-status">
      Stan Gry: {{ gameStatus }} | Czas: {{ formatTime(gameTimeLeft) }}
    </div>

    <nav class="tabs">
      <button @click="activeTab = 'map'" :class="{ 'active': activeTab === 'map' }">Mapa</button>
      <button @click="activeTab = 'profile'" :class="{ 'active': activeTab === 'profile' }">Profile</button>
      <button @click="activeTab = 'tags'" :class="{ 'active': activeTab === 'tags' }">Tagi</button>
      <button @click="activeTab = 'config'" :class="{ 'active': activeTab === 'config' }">Konfiguracja</button>
    </nav>

    <main class="tab-content">
      <div v-if="activeTab === 'map'" class="tab-pane no-padding">
        <TacticalMap :players="players" :isActive="activeTab === 'map'" />
      </div>

      <div v-if="activeTab === 'profile'" class="tab-pane">
        <h2>Profile Graczy</h2>
        <ProfileTab
          :profiles="profiles"
          @add-profile="showAddProfile = true"
          @edit-profile="editProfile"
          @delete-profile="deleteProfile"
        />
      </div>

      <div v-if="activeTab === 'tags'" class="tab-pane">
        <TagsTab
          :players="players"
          :show-spoof-panel="showSpoofPanel"
          :spoof-form="spoofForm"
          @spoof="startSpoofing"
          @submit-spoof="submitSpoof"
          @cancel-spoof="cancelSpoof"
        />
      </div>

      <div v-if="activeTab === 'config'" class="tab-pane">
        <h2>Konfiguracja</h2>
        <ConfigTab
          :players="players"
          :profiles="profiles"
          :profile-assignments="profileAssignments"
          :team-assignments="teamAssignments"
          :session-form="sessionForm"
          @assign-profile-team="assignProfileAndTeam"
          @set-game-mode="setGameMode"
          @start-game="startGame"
          @stop-game="stopGame"
          @reset-game="resetGame"
        />
      </div>
    </main>

    <ProfileModal
      :show="showAddProfile || editingProfile"
      :editing-id="currentEditingId"
      :form="profileForm"
      @save="saveProfile"
      @cancel="cancelProfile"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import TacticalMap from './components/TacticalMap.vue'
import ProfileTab from './components/ProfileTab.vue'
import TagsTab from './components/TagsTab.vue'
import ConfigTab from './components/ConfigTab.vue'
import ProfileModal from './components/ProfileModal.vue'

// --- STAN APLIKACJI ---
const players = ref({})
const isConnected = ref(false)
const activeTab = ref('tags')
const currentTime = ref('')
const gameStatus = ref('configuration')
const gameTimeLeft = ref(0)

let socket = null
let clockInterval = null
let gameTimer = null

// --- STAN SPOOFOWANIA ---
const showSpoofPanel = ref(false)
const spoofForm = ref({ dev_eui: '', lat: 0, lon: 0 })

// --- STAN PROFILI ---
const profiles = ref({})
const showAddProfile = ref(false)
const editingProfile = ref(false)
const currentEditingId = ref(null)
const profileForm = ref({ nick: '', role: '' })
const sessionForm = ref({ mode_id: '1', time_mins: 60 })
const teamAssignments = ref({})
const profileAssignments = ref({})

// --- FUNKCJE POMOCNICZE ---
function updateClock() {
  currentTime.value = new Date().toLocaleTimeString('pl-PL')
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

// --- FUNKCJE PROFILI ---
async function fetchProfiles() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/profiles')
    profiles.value = await res.json()
  } catch (e) { console.error(e) }
}

function editProfile(id) {
  currentEditingId.value = id
  editingProfile.value = true
  profileForm.value = { ...profiles.value[id] }
}

async function deleteProfile(id) {
  try {
    await fetch(`http://127.0.0.1:8000/api/profiles/${id}`, { method: 'DELETE' })
    await fetchProfiles()
  } catch (e) { console.error(e) }
}

function cancelProfile() {
  showAddProfile.value = false
  editingProfile.value = false
  currentEditingId.value = null
  profileForm.value = { nick: '', role: '' }
}

async function saveProfile() {
  const method = currentEditingId.value ? 'PUT' : 'POST'
  const url = currentEditingId.value ? `http://127.0.0.1:8000/api/profiles/${currentEditingId.value}` : 'http://127.0.0.1:8000/api/profiles'
  try {
    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileForm.value)
    })
    await fetchProfiles()
    cancelProfile()
  } catch (e) { console.error(e) }
}

// --- FUNKCJE SPOOFOWANIA ---
function startSpoofing(devEui, lat, lon) {
  showSpoofPanel.value = true
  spoofForm.value = { dev_eui: devEui, lat, lon }
}

function cancelSpoof() {
  showSpoofPanel.value = false
}

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

// --- FUNKCJE GRY ---
async function setGameMode() {
  try {
    await fetch('http://127.0.0.1:8000/api/game/mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode_id: sessionForm.value.mode_id })
    })
  } catch (e) { console.error(e) }
}

async function startGame() {
  try {
    await fetch('http://127.0.0.1:8000/api/game/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ time_mins: sessionForm.value.time_mins })
    })
    gameTimeLeft.value = sessionForm.value.time_mins * 60
    gameStatus.value = 'running'
    gameTimer = setInterval(() => {
      if (gameTimeLeft.value > 0) {
        gameTimeLeft.value--
      } else {
        clearInterval(gameTimer)
        gameStatus.value = 'stopped'
      }
    }, 1000)
  } catch (e) { console.error(e) }
}

async function stopGame() {
  try {
    await fetch('http://127.0.0.1:8000/api/game/stop', { method: 'POST' })
    if (gameTimer) clearInterval(gameTimer)
    gameStatus.value = 'stopped'
  } catch (e) { console.error(e) }
}

async function resetGame() {
  try {
    await fetch('http://127.0.0.1:8000/api/game/reset', { method: 'POST' })
    if (gameTimer) clearInterval(gameTimer)
    gameStatus.value = 'configuration'
    gameTimeLeft.value = 0
  } catch (e) { console.error(e) }
}

async function assignProfileAndTeam(devEui) {
  const newProfile = profileAssignments.value[devEui]
  const newTeam = teamAssignments.value[devEui]
  try {
    await Promise.all([
      fetch(`http://127.0.0.1:8000/api/players/${devEui}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: newProfile })
      }),
      fetch(`http://127.0.0.1:8000/api/players/${devEui}/team`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team: parseInt(newTeam) })
      })
    ])
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
    try {
      const msg = JSON.parse(event.data)
      if (msg.type === "UPDATE_PLAYERS" && msg.data) {
        players.value = msg.data

        Object.keys(msg.data).forEach(devEui => {
          if (profileAssignments.value[devEui] === undefined) {
            profileAssignments.value[devEui] = msg.data[devEui].profile_id || ""
          }
          if (teamAssignments.value[devEui] === undefined) {
            teamAssignments.value[devEui] = msg.data[devEui].team?.toString() || "0"
          }
        })

        gameStatus.value = msg.game_status || gameStatus.value
        gameTimeLeft.value = msg.time_left || gameTimeLeft.value
      }
    } catch (e) {
      console.error("Błąd parsowania WS:", e)
    }
  }

  fetchProfiles()
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

.game-status { font-size: 0.9rem; margin: 10px 0; }

.tabs button { background: #1a1a1a; border: 1px solid #333; color: #777; padding: 12px 25px; cursor: pointer; transition: 0.2s; }
.tabs button.active { background: #222; color: #00ff00; border-bottom: 2px solid #00ff00; }

.tab-pane { background: #111; border: 1px solid #222; padding: 20px; min-height: 60vh; }
.no-padding { padding: 0; }
</style>
