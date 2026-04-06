<template>
  <div id="leaflet-map" class="map-container"></div>
</template>

<script setup>
import { onMounted, watch, ref, nextTick } from 'vue'
import L from 'leaflet'
// Absolutnie kluczowe: importujemy style CSS dla Leaflet!
import 'leaflet/dist/leaflet.css'

// Otrzymujemy dane od graczy od rodzica (App.vue)
const props = defineProps({
  players: Object,
  isActive: Boolean // Czy mapa jest teraz widoczna (aktywna zakładka)
})

const map = ref(null)
const markers = ref({}) // Słownik do przechowywania markerów

// Funkcja inicjalizująca mapę
function initMap() {
  if (map.value) return; // Zapobiega podwójnemu renderowaniu

  // Tworzymy mapę z bazowym widokiem (np. środek poligonu)
  map.value = L.map('leaflet-map').setView([51.10788, 17.03854], 14);

  // Dodajemy darmową warstwę OpenStreetMap
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map.value);
}

// Obserwujemy zmiany w danych graczy (z WebSocket)
watch(() => props.players, (newPlayers) => {
  if (!map.value) return;

  // Usuwamy markery graczy, którzy już nie istnieją
  Object.keys(markers.value).forEach(devEui => {
    if (!newPlayers[devEui]) {
      map.value.removeLayer(markers.value[devEui]);
      delete markers.value[devEui];
    }
  });

  // Dodajemy lub aktualizujemy istniejące markery
  Object.entries(newPlayers).forEach(([devEui, data]) => {
    if (markers.value[devEui]) {
      // Aktualizacja pozycji
      markers.value[devEui].setLatLng([data.lat, data.lon]);
    } else {
      // Stworzenie nowego markera z Popupem
      const marker = L.marker([data.lat, data.lon]).addTo(map.value);
      marker.bindPopup(`Gracz: ${devEui}`);
      markers.value[devEui] = marker;
    }
  });
}, { deep: true });

// Jeśli zakładka się przełączy na mapę, musimy ją "odświeżyć"
watch(() => props.isActive, (newActive) => {
  if (newActive) {
    // nextTick upewnia się, że DOM jest już zaktualizowany
    nextTick(() => {
      if (!map.value) initMap();
      map.value.invalidateSize(); // Kluczowe dla Leaflet przy ukrywaniu/pokazywaniu
    });
  }
});

// Startujemy, gdy komponent się załaduje
onMounted(() => {
  // Nie inicjalizujemy tutaj, jeśli domyślna zakładka to nie 'map'
  if (props.isActive) initMap();
})
</script>

<style scoped>
.map-container {
  height: calc(100vh - 200px); /* Mapa na prawie całą wysokość ekranu */
  width: 100%;
  border: 1px solid #333;
}
</style>