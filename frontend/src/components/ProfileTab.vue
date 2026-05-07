<template>
  <div class="profiles-section">
    <button @click="$emit('add-profile')" class="btn-add">Dodaj Profil</button>

    <table class="tactical-table">
      <thead>
      <tr>
        <th>ID</th>
        <th>Nick</th>
        <th>Rola</th>
        <th>Gry</th>
        <th>Zabicia</th>
        <th>Akcje</th>
      </tr>
      </thead>

      <tbody>
      <tr v-for="(profile, id) in profiles" :key="id">
        <td>{{ id }}</td>
        <td>{{ profile.nick }}</td>
        <td>{{ profile.role }}</td>
        <td>{{ profile.games_count }}</td>
        <td>{{ profile.killed_count }}</td>
        <td>
          <button @click="$emit('edit-profile', id)" class="btn-edit">Edytuj</button>
          <button @click="$emit('delete-profile', id)" class="btn-delete">Usuń</button>
        </td>
      </tr>

      <tr v-if="Object.keys(profiles).length === 0">
        <td colspan="6">Brak profili...</td>
      </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  profiles: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['add-profile', 'edit-profile', 'delete-profile'])
</script>

<style scoped>
.profiles-section {
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

.btn-add {
  background: #008cba;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
  margin-bottom: 10px;
}

.btn-edit {
  background: #ffa500;
  color: white;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
  margin-right: 5px;
}

.btn-delete {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
}
</style>
