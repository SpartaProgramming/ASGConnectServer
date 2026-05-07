<template>
  <div class="assigned-players-section">
    <h3>Aktywni Gracze</h3>

    <table class="tactical-table">
      <thead>
      <tr>
        <th>DevEUI</th>
        <th>Nick</th>
        <th>Profil</th>
        <th>Drużyna</th>
      </tr>
      </thead>

      <tbody>
      <template v-for="(data, devEui) in players" :key="devEui">
        <tr v-if="data && data.profile_id">
          <td>{{ devEui }}</td>
          <td>{{ data.nickname || 'N/A' }}</td>
          <td>{{ data.profile_id }}</td>
          <td>{{ data.team === 0 ? 'RED' : 'BLUE' }}</td>
        </tr>
      </template>

      <tr v-if="!players || Object.values(players).filter(p => p && p.profile_id).length === 0">
        <td colspan="4">Brak aktywnych graczy...</td>
      </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  players: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.assigned-players-section {
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
</style>
