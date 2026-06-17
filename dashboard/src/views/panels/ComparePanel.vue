<template>
  <div>
    <div v-if="!runId" class="card card-pad empty-hint">请先选择 Run，查看概览 / 写入 / 检索对比。</div>
    <RunDetail v-else :run-id="runId" embedded :key="runId + '-' + refreshTick" />
  </div>
</template>

<script setup>
import { inject, ref } from "vue";
import RunDetail from "../RunDetail.vue";

defineProps({ runId: { type: String, default: "" } });
const refreshTick = inject("refreshTick", ref(0));
</script>
