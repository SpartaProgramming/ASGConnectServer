<template>
  <div class="session-section">
    <h3>Konfiguracja Sesji Gry</h3>

    <div class="session-form">
      <label>
        Tryb Gry:
        <select v-model="sessionForm.mode_id">
          <option value="1">Team Deathmatch</option>
          <option value="2">Capture the Flag</option>
          <option value="3">King of the Hill</option>
        </select>
      </label>

      <label>
        Czas (min):
        <input v-model.number="sessionForm.time_mins" type="number" min="1">
      </label>

      <button @click="$emit('set-game-mode')" class="btn-set">
        Wyślij Konfigurację
      </button>
    </div>

    <div class="game-controls">
      <button @click="$emit('start-game')" class="btn-start">Start Gry</button>
      <button @click="$emit('stop-game')" class="btn-stop">Stop Gry</button>
      <button @click="$emit('reset-game')" class="btn-reset">Reset</button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  sessionForm: {
    type: Object,
    default: () => ({ mode_id: '1', time_mins: 60 })
  }
})

defineEmits(['set-game-mode', 'start-game', 'stop-game', 'reset-game'])
</script>

<style scoped>
.session-section {
  margin-bottom: 20px;
}

.session-form label {
  display: block;
  margin-bottom: 10px;
}

.session-form select,
.session-form input {
  padding: 5px;
  background: #222;
  color: #d0d0d0;
  border: 1px solid #444;
  margin-bottom: 10px;
}

.btn-set {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}

.game-controls {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.btn-start {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}

.btn-stop {
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}

.btn-reset {
  background: #ffc107;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}

</style>