<template>
  <div v-if="loading" class="muted">Loading run {{ runId }}…</div>
  <div v-else-if="error" class="error-box">{{ error }}</div>
  <div v-else-if="data">
    <div v-if="!embedded" class="toolbar">
      <div>
        <h2 class="section-title" style="margin: 0">Run {{ runId }}</h2>
        <div class="muted">Single-run comparison · TiMEM vs MemOS vs Mem0</div>
      </div>
      <select v-model="mode" v-if="modes.length">
        <option v-for="m in modes" :key="m" :value="m">Retrieval {{ m }}</option>
      </select>
    </div>
    <div v-else class="section-header">
      <h2 class="section-title">对比 · {{ runId }}</h2>
      <select v-model="mode" v-if="modes.length" class="form-input" style="width: auto; margin-top: 8px">
        <option v-for="m in modes" :key="m" :value="m">Retrieval {{ m }}</option>
      </select>
    </div>

    <RunConfigBar
      :ingest="data.ingest"
      :retrieval="retrievalBlob"
      :job="data.job"
    />

    <div v-if="missingIngest" class="error-box" style="margin-bottom: 16px">
      <strong>未写入记忆：</strong>本 Run 没有 <code>ingest.json</code>（只跑了检索）。数据库里没有该 run 的用户记忆，所以
      Recall / Judge 为 0、EMPTY=题目数。请到「实验」页对该 Run 点 <strong>一键 Full</strong>，或先
      <strong>仅 Ingest</strong> 再跑 T0。
    </div>

    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        :class="['tab', tab === t.id ? 'active' : '']"
        @click="tab = t.id"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Overview -->
    <div v-show="tab === 'overview'" class="grid-systems">
      <div v-for="sys in SYSTEMS" :key="sys.id" class="card card-pad">
        <SystemMetrics
          :system="sys.id"
          :label="sys.label"
          :ingest="data.ingest?.[sys.id]"
          :retrieval="retrievalBlob[sys.id]"
        />
      </div>
    </div>

    <!-- Efficiency -->
    <div v-show="tab === 'efficiency'">
      <EfficiencyCompareTable
        :retrieval="retrievalBlob"
        :reference-baselines="data.reference_baselines"
      />
    </div>

    <!-- Ingest -->
    <div v-show="tab === 'ingest'">
      <IngestCompareTable
        :systems="SYSTEM_IDS"
        :details-by-system="ingestDetailsBySystem"
      />
    </div>

    <!-- Retrieval -->
    <div v-show="tab === 'retrieval'">
      <RetrievalCompareTable
        :systems="SYSTEM_IDS"
        :details-by-system="retrievalDetailsBySystem"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from "vue";
import { SYSTEM_IDS, SYSTEMS } from "../constants/systems";
import { fetchRun } from "../api";
import RunConfigBar from "../components/RunConfigBar.vue";
import SystemMetrics from "../components/SystemMetrics.vue";
import IngestCompareTable from "../components/IngestCompareTable.vue";
import RetrievalCompareTable from "../components/RetrievalCompareTable.vue";
import EfficiencyCompareTable from "../components/EfficiencyCompareTable.vue";

const props = defineProps({
  runId: { type: String, required: true },
  embedded: { type: Boolean, default: false },
});

const data = ref(null);
const loading = ref(true);
const error = ref("");
const refreshTick = inject("refreshTick", ref(0));
const tab = ref("overview");
const mode = ref("T0");

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "efficiency", label: "Efficiency" },
  { id: "ingest", label: "Ingest" },
  { id: "retrieval", label: "Retrieval" },
];

const modes = computed(() => Object.keys(data.value?.retrieval || {}));

const missingIngest = computed(() => !data.value?.ingest && Object.keys(data.value?.retrieval || {}).length > 0);

const retrievalBlob = computed(() => data.value?.retrieval?.[mode.value] || {});

const retrievalDetailsBySystem = computed(() => {
  const blob = retrievalBlob.value;
  const out = {};
  for (const id of SYSTEM_IDS) {
    out[id] = blob[id]?.details || [];
  }
  return out;
});

const ingestDetailsBySystem = computed(() => {
  const ing = data.value?.ingest;
  if (!ing) return {};
  return Object.fromEntries(SYSTEM_IDS.map((id) => [id, ing[id]?.details || []]));
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await fetchRun(props.runId);
    const m = Object.keys(data.value.retrieval || {});
    mode.value = m.includes("T0") ? "T0" : m[0] || "T0";
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => props.runId, load);
watch(refreshTick, load);
</script>
