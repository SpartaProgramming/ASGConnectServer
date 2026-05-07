<template>
  <div v-if="show" class="modal">
    <div class="modal-content">
      <h3>{{ editingId ? 'Edytuj Profil' : 'Dodaj Profil' }}</h3>

      <input v-model="form.nick" placeholder="Nick" />
      <input v-model="form.role" placeholder="Rola" />

      <button @click="$emit('save')" class="btn-save">Zapisz</button>
      <button @click="$emit('cancel')" class="btn-cancel">Anuluj</button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  show: {
    type: Boolean,
    default: false
  },
  editingId: {
    type: String,
    default: null
  },
  form: {
    type: Object,
    default: () => ({ nick: '', role: '' })
  }
})

defineEmits(['save', 'cancel'])
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: #1a1a1a;
  padding: 20px;
  border-radius: 5px;
  width: 300px;
}

.modal-content h3 {
  margin-top: 0;
}

.modal-content input {
  display: block;
  width: 100%;
  padding: 8px;
  margin-bottom: 10px;
  background: #222;
  color: #d0d0d0;
  border: 1px solid #444;
}

.btn-save {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
  margin-right: 10px;
}

.btn-cancel {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}
</style>
