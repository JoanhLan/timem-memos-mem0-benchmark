<template>
  <div v-if="hasContent" class="card card-pad run-config-bar" style="margin-bottom: 16px">
    <h3 class="section-title" style="margin-top: 0; font-size: 14px">Run 配置</h3>
    <div class="config-chips">
      <span v-if="jobOpts.fixture != null" class="chip">数据集: {{ jobOpts.fixture ? "Fixture" : "LoCoMo" }}</span>
      <span v-if="jobOpts.persona_count != null" class="chip">Personas: {{ jobOpts.persona_count }}</span>
      <span v-if="jobSystems.length" class="chip">系统: {{ jobSystems.join(", ") }}</span>
      <span v-if="retrievalPreset" class="chip">Preset: {{ retrievalPreset }}</span>
      <span v-if="retrievalTopK != null" class="chip">top_k: {{ retrievalTopK }}</span>
      <template v-for="(cfg, sys) in ingestConcurrency" :key="sys">
        <span class="chip">
          {{ sys }} ingest: {{ cfg.effective_session_concurrency ?? cfg.session_concurrency }} parallel
          <template v-if="cfg.mem0_poll_mode"> · poll={{ cfg.mem0_poll_mode }}</template>
        </span>
      </template>
      <span v-if="ingestSystemParallel != null" class="chip">
        ingest system_parallel: {{ ingestSystemParallel ? "yes" : "no" }}
      </span>
      <template v-if="retrievalConcurrency">
        <span v-if="retrievalConcurrency.query_concurrency != null" class="chip">
          query: {{ retrievalConcurrency.query_concurrency }}
        </span>
        <span v-if="retrievalConcurrency.timem_query_concurrency != null" class="chip">
          timem query: {{ retrievalConcurrency.timem_query_concurrency }}
        </span>
        <span v-if="retrievalConcurrency.effective_query_concurrency != null" class="chip">
          effective query: {{ retrievalConcurrency.effective_query_concurrency }}
        </span>
        <span v-if="retrievalConcurrency.judge_concurrency != null" class="chip">
          judge: {{ retrievalConcurrency.judge_concurrency }}
        </span>
        <span v-if="retrievalConcurrency.backfill_concurrency != null" class="chip">
          backfill: {{ retrievalConcurrency.backfill_concurrency }}
        </span>
        <span v-if="retrievalConcurrency.pipeline_mode != null" class="chip">
          pipeline: {{ retrievalConcurrency.pipeline_mode ? "yes" : "no" }}
        </span>
        <span v-if="retrievalConcurrency.system_parallel != null" class="chip">
          retrieval system_parallel: {{ retrievalConcurrency.system_parallel ? "yes" : "no" }}
        </span>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { SYSTEM_IDS } from "../constants/systems";

const props = defineProps({
  ingest: { type: Object, default: () => ({}) },
  retrieval: { type: Object, default: () => ({}) },
  job: { type: Object, default: null },
});

const jobOpts = computed(() => props.job?.options || {});

const jobSystems = computed(() => {
  const s = jobOpts.value.systems;
  if (Array.isArray(s)) return s;
  return [];
});

const retrievalPreset = computed(() => {
  for (const id of SYSTEM_IDS) {
    const p = props.retrieval?.[id]?.preset;
    if (p) return p;
  }
  return null;
});

const retrievalTopK = computed(() => {
  for (const id of SYSTEM_IDS) {
    const k = props.retrieval?.[id]?.top_k;
    if (k != null) return k;
  }
  return null;
});

const ingestConcurrency = computed(() => {
  const out = {};
  for (const id of SYSTEM_IDS) {
    const cfg = props.ingest?.[id]?.concurrency_settings;
    if (cfg && Object.keys(cfg).length) out[id] = cfg;
  }
  return out;
});

const ingestSystemParallel = computed(() => {
  for (const id of SYSTEM_IDS) {
    const v = props.ingest?.[id]?.concurrency_settings?.system_parallel;
    if (v != null) return v;
  }
  return null;
});

const retrievalConcurrency = computed(() => {
  for (const id of SYSTEM_IDS) {
    const cfg = props.retrieval?.[id]?.concurrency_settings;
    if (cfg && Object.keys(cfg).length) return cfg;
  }
  return null;
});

const hasContent = computed(
  () =>
    retrievalPreset.value ||
    retrievalTopK.value != null ||
    Object.keys(ingestConcurrency.value).length ||
    retrievalConcurrency.value ||
    jobSystems.value.length ||
    jobOpts.value.fixture != null
);
</script>

<style scoped>
.config-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  font-size: 12px;
  padding: 4px 10px;
  background: #f1f5f9;
  border-radius: 6px;
  color: #334155;
}
</style>
