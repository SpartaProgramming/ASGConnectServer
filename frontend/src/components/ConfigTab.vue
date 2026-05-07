<template>
  <div class="config-sections">
    <ActivePlayersSection
        :players="players"
        :profiles="profiles"
        :profile-assignments="profileAssignments"
        :team-assignments="teamAssignments"
        @assign-profile-team="$emit('assign-profile-team', $event)"
    />

    <AssignedPlayersSection :players="players" />

    <SessionSection
        :session-form="sessionForm"
        @set-game-mode="$emit('set-game-mode')"
        @start-game="$emit('start-game')"
        @stop-game="$emit('stop-game')"
        @reset-game="$emit('reset-game')"
    />
  </div>
</template>

<script setup>
import ActivePlayersSection from './ActivePlayersSection.vue'
import AssignedPlayersSection from './AssignedPlayersSection.vue'
import SessionSection from './SessionSection.vue'

defineProps({
  players: {
    type: Object,
    default: () => ({})
  },
  profiles: {
    type: Object,
    default: () => ({})
  },
  profileAssignments: {
    type: Object,
    default: () => ({})
  },
  teamAssignments: {
    type: Object,
    default: () => ({})
  },
  sessionForm: {
    type: Object,
    default: () => ({ mode_id: '1', time_mins: 60 })
  }
})

defineEmits([
  'assign-profile-team',
  'set-game-mode',
  'start-game',
  'stop-game',
  'reset-game'
])
</script>

<style scoped>
.config-sections {
  display: block;
}
</style>
