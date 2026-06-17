<template>
  <div class="metric">
    <div class="label">{{ label }}</div>
    <div class="value">{{ value }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
});
</script>
