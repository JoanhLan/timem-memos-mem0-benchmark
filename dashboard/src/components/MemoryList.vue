<template>
  <div>
    <div v-if="!records?.length" class="muted">No records</div>
    <div
      v-for="(r, i) in records"
      :key="i"
      :class="['memory-item', !(r.content || '').trim() ? 'empty' : '']"
    >
      <div class="memory-meta">
        #{{ i + 1 }}
        <span v-if="r.type"> · {{ r.type }}</span>
        <span v-if="r.layer"> · {{ r.layer }}</span>
        <span v-if="r.score != null"> · score {{ r.score }}</span>
      </div>
      <div v-if="(r.content || '').trim()" v-html="highlightGold(r.content, gold)"></div>
      <div v-else class="muted">(empty content)</div>
    </div>
  </div>
</template>

<script setup>
import { highlightGold } from "../utils";

defineProps({
  records: { type: Array, default: () => [] },
  gold: { type: String, default: "" },
});
</script>
