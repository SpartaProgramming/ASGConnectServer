<template>
  <div class="active-players-section">
    <h3>Konfigurowanie Aktywnych Graczy</h3>

    <table class="tactical-table">
      <thead>
      <tr>
        <th>DevEUI</th>
        <th>Wybór Profilu</th>
        <th>Drużyna</th>
        <th>Akcja</th>
      </tr>
      </thead>

      <tbody>
      <tr v-for="(data, devEui) in players" :key="devEui">
        <td>{{ devEui }}</td>

        <td>
          <select v-model="profileAssignments[devEui]">
            <option value="">None</option>
            <option
                v-for="(profile, id) in profiles"
                :key="id"
                :value="id"
            >
              {{ profile.nick }}
            </option>
          </select>
        </td>

        <td>
          <select v-model="teamAssignments[devEui]">
            <option value="0">RED</option>
            <option value="1">BLUE</option>
          </select>
        </td>

        <td>
          <button
              class="btn-assign"
              @click="$emit('assign-profile-team', devEui)"
          >
            Przypisz Profil
          </button>
        </td>
      </tr>

      <tr v-if="Object.keys(players).length === 0">
        <td colspan="4">Brak graczy...</td>
      </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  players: { type: Object, default: () => ({}) },
  profiles: { type: Object, default: () => ({}) },
  profileAssignments: { type: Object, default: () => ({}) },
  teamAssignments: { type: Object, default: () => ({}) }
})

defineEmits(['assign-profile-team'])
</script>

<style scoped>
.active-players-section {
  margin-bottom: 20px;
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

.btn-assign {
  background: #007bff;
  color: white;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
}
</style>
