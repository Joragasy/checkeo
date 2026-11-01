<script setup lang="ts">
defineProps<{ color: string; size: string; opacity?: number }>()
</script>

<template>
  <span class="dot" :style="{ background: color, opacity, width: size, height: size }" />
</template>

<style scoped>
.dot {
  display: inline-block;
  border-radius: 50%;
}
</style>
