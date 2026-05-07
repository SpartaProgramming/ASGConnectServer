<template>
  <div class="tags-layout">
    <div class="tags-table-wrapper">
      <h2>Status Urządzeń w Terenie</h2>

      <table class="tactical-table">
        <thead>
        <tr>
          <th>ID (DevEUI)</th>
          <th>Status</th>
          <th>Up Count</th>
          <th>Down Count</th>
          <th>Sygnał</th>
          <th>Last Seen</th>
          <th>Akcje</th>
        </tr>
        </thead>

        <tbody>
        <tr v-for="(data, devEui) in players" :key="devEui">
          <td class="player-id">{{ devEui }}</td>

          <td>
              <span :class="getTagConnectionStatus(data).class">
                {{ getTagConnectionStatus(data).label }}
              </span>
          </td>

          <td>{{ data.uplink_count || 0 }}</td>
          <td>{{ data.downlink_count || 0 }}</td>
          <td>{{ data.rssi }} dBm</td>
          <td>{{ formatLastSeen(data.last_seen) }}</td>

          <td>
            <button
                @click="$emit('spoof', devEui, data.lat, data.lon)"
                class="btn-spoof"
            >
              SPOOF
            </button>
          </td>
        </tr>

        <tr v-if="Object.keys(players).length === 0">
          <td colspan="7">Brak aktywnych jednostek...</td>
        </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showSpoofPanel" class="admin-panel spoof-pane">
      <h2>GPS Spoofing</h2>

      <div class="spoof-form">
        <label>
          Urządzenie:
          <strong class="player-id">{{ spoofForm.dev_eui }}</strong>
        </label>

        <div class="input-group">
          <input v-model.number="spoofForm.lat" type="number" step="0.0001" placeholder="Lat">
          <input v-model.number="spoofForm.lon" type="number" step="0.0001" placeholder="Lon">
        </div>

        <div class="action-group">
          <button @click="$emit('submit-spoof')" class="btn-attack">WYŚLIJ POZYCJĘ</button>
          <button @click="$emit('cancel-spoof')" class="btn-close">Anuluj</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  players: {
    type: Object,
    default: () => ({})
  },
  showSpoofPanel: {
    type: Boolean,
    default: false
  },
  spoofForm: {
    type: Object,
    default: () => ({ dev_eui: '', lat: 0, lon: 0 })
  }
})

defineEmits(['spoof', 'submit-spoof', 'cancel-spoof'])

function formatLastSeen(timestamp) {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('pl-PL')
}

function getTagConnectionStatus(data) {
  if (!data.last_seen) {
    return { label: 'INICJACJA', class: 'status-unknown' }
  }

  const now = Date.now() / 1000
  const timeDiff = now - data.last_seen

  if (timeDiff < 60) {
    return { label: 'ONLINE', class: 'status-online' }
  } else if (timeDiff < 300) {
    return { label: 'TIMEOUT', class: 'status-timeout' }
  } else {
    return { label: 'OFFLINE', class: 'status-offline' }
  }
}
</script>

<style scoped>
.tags-layout {
  display: flex;
  gap: 20px;
}

.tags-table-wrapper {
  flex: 1;
}

.tactical-table {
  width: 100%;
  border-collapse: collapse;
}

.tactical-table th {
  background: #1a1a1a;
  color: #00ff00;
  padding: 15px;
  text-align: left;
}

.tactical-table td {
  padding: 12px;
  border-bottom: 1px solid #222;
}

.player-id {
  font-family: monospace;
  font-weight: bold;
}

.btn-spoof {
  background: #6a1b9a;
  color: white;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
}

.admin-panel {
  background: #1a1a1a;
  border: 1px solid #333;
  padding: 20px;
  border-radius: 5px;
}

.spoof-pane {
  max-width: 400px;
}

.spoof-form label {
  display: block;
  margin-bottom: 10px;
}

.input-group {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.input-group input {
  padding: 5px;
  background: #222;
  color: #d0d0d0;
  border: 1px solid #444;
}

.action-group {
  display: flex;
  gap: 10px;
}

.btn-attack {
  background: #006400;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}

.btn-close {
  background: #444;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}

.status-online {
  color: #00ff00;
  border: 1px solid #00ff00;
  padding: 2px 6px;
  border-radius: 3px;
}

.status-timeout {
  color: #ff9800;
  border: 1px solid #ff9800;
  padding: 2px 6px;
  border-radius: 3px;
  animation: blink 2s infinite;
}

.status-offline {
  color: #ff0000;
  border: 1px solid #ff0000;
  padding: 2px 6px;
  border-radius: 3px;
}

.status-unknown {
  color: #555;
  border: 1px solid #555;
  padding: 2px 6px;
  border-radius: 3px;
}

@keyframes blink {
  50% { opacity: 0.5; }
}
</style>
