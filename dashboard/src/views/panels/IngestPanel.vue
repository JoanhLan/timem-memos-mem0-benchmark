<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">写入 / Ingest</h2>
      <p class="muted">TiMEM、MemOS、Mem0 按 persona / session 对称明细</p>
    </div>

    <div v-if="!runId" class="card card-pad empty-hint">请先选择 Run。</div>
    <div v-else-if="loading" class="muted">加载中…</div>
    <div v-else-if="error" class="error-box">{{ error }}</div>
    <div v-else-if="data">
      <div class="grid-systems" style="margin-bottom: 16px">
        <div v-for="sys in SYSTEMS" :key="sys.id" class="card card-pad">
          <h3><span :class="['badge', sys.badge]">{{ sys.label }}</span></h3>
          <p class="muted">{{ summary(data.ingest?.[sys.id]) }}</p>
        </div>
      </div>
      <IngestCompareTable
        style="margin-top: 16px"
        :systems="SYSTEM_IDS"
        :details-by-system="ingestDetailsBySystem"
      />
    </div>
    <div v-else class="card card-pad empty-hint">尚无 ingest 报告，请在「实验」页运行 Ingest。</div>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue";
import { SYSTEM_IDS, SYSTEMS } from "../../constants/systems";
import { fetchRun } from "../../api";
import IngestCompareTable from "../../components/IngestCompareTable.vue";

const props = defineProps({ runId: { type: String, default: "" } });
const refreshTick = inject("refreshTick", ref(0));

const data = ref(null);
const loading = ref(false);
const error = ref("");

const ingestDetailsBySystem = computed(() => {
  const ing = data.value?.ingest;
  if (!ing) return {};
  return Object.fromEntries(SYSTEM_IDS.map((id) => [id, ing[id]?.details || []]));
});

function summary(block) {
  if (!block) return "—";
  const addCount = block.add_count ?? block.session_count;
  const addOk = block.add_success_count ?? block.success_count;
  const p50 = block.add_latency?.p50 ?? block.latency?.p50 ?? 0;
  const est = block.add_latency_estimated ? " (est.)" : "";
  const sessions = block.session_count != null ? ` · ${block.success_count}/${block.session_count} sessions` : "";
  return `${addOk}/${addCount} adds OK · p50 ${Math.round(p50)} ms${est}${sessions}`;
}

async function load() {
  if (!props.runId) {
    data.value = null;
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    data.value = await fetchRun(props.runId);
  } catch (e) {
    error.value = e.message;
    data.value = null;
  } finally {
    loading.value = false;
  }
}

watch(() => props.runId, load, { immediate: true });
watch(refreshTick, load);
</script>
