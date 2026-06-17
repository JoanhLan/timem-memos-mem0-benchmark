<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">检索 / Retrieval</h2>
      <p class="muted">跑 T0 / T1 并查看题目级对比（配置与「实验」页同步）</p>
    </div>

    <div v-if="!runId" class="card card-pad empty-hint">请先选择 Run。</div>
    <template v-else>
      <div class="card card-pad" style="margin-bottom: 16px">
        <RunOptionsForm :opts="opts" :show-skip-t1="false" />
        <div class="btn-row">
          <button class="btn btn-primary" type="button" :disabled="busy" @click="runMode('T0')">跑 T0</button>
          <button class="btn" type="button" :disabled="busy" @click="runMode('T1')">跑 T1（含 backfill）</button>
          <button
            class="btn"
            type="button"
            :disabled="busy || !opts.hasBackfillLayers.value"
            @click="runBackfill"
          >
            仅 TiMEM Backfill
          </button>
          <button class="btn btn-sm" type="button" @click="load">刷新报告</button>
        </div>
        <p v-if="msg" :class="msgOk ? 'hint' : 'error-box'" style="margin-top: 12px">{{ msg }}</p>
      </div>

      <div v-if="loading" class="muted">加载报告…</div>
      <template v-else-if="data && modes.length">
        <div class="toolbar">
          <select v-model="mode" class="form-input" style="width: auto">
            <option v-for="m in modes" :key="m" :value="m">Retrieval {{ m }}</option>
          </select>
        </div>
        <div class="grid-systems" style="margin-bottom: 16px">
          <div v-for="sys in SYSTEMS" :key="sys.id" class="card card-pad">
            <SystemMetrics
              :system="sys.id"
              :label="sys.label"
              :ingest="data?.ingest?.[sys.id]"
              :retrieval="retrievalBlockFull(sys.id)"
            />
          </div>
        </div>
        <RetrievalCompareTable
          :systems="opts.systemsList()"
          :details-by-system="retrievalDetailsBySystem"
        />
      </template>
      <div v-else class="card card-pad empty-hint">
        <template v-if="data && !data.ingest">
          已有检索报告但<strong>没有 Ingest</strong>，召回为空是正常的。请到「实验」页运行「一键 Full」或「仅 Ingest」。
        </template>
        <template v-else>尚无 retrieval 报告，请先运行 Ingest 再跑 T0/T1。</template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue";
import { SYSTEMS } from "../../constants/systems";
import RetrievalCompareTable from "../../components/RetrievalCompareTable.vue";
import RunOptionsForm from "../../components/RunOptionsForm.vue";
import SystemMetrics from "../../components/SystemMetrics.vue";
import { useBenchmarkOptions } from "../../composables/useBenchmarkOptions";
import { fetchRun, startJob } from "../../api";

const props = defineProps({ runId: { type: String, default: "" } });
const emit = defineEmits(["job-started"]);
const refreshTick = inject("refreshTick", ref(0));

const opts = useBenchmarkOptions();
const data = ref(null);
const loading = ref(false);
const busy = ref(false);
const msg = ref("");
const msgOk = ref(false);
const mode = ref("T0");

const modes = computed(() => Object.keys(data.value?.retrieval || {}));

const retrievalDetailsBySystem = computed(() => {
  const blob = data.value?.retrieval?.[mode.value] || {};
  const out = {};
  for (const sys of SYSTEMS) {
    out[sys.id] = blob[sys.id]?.details || [];
  }
  return out;
});

function retrievalBlockFull(system) {
  return data.value?.retrieval?.[mode.value]?.[system] || null;
}

function retrievalBlock(system) {
  return retrievalBlockFull(system);
}

async function load() {
  if (!props.runId) return;
  loading.value = true;
  msg.value = "";
  try {
    data.value = await fetchRun(props.runId);
    const m = modes.value;
    if (m.length && !m.includes(mode.value)) mode.value = m[0];
  } catch (e) {
    msg.value = e.message;
    msgOk.value = false;
  } finally {
    loading.value = false;
  }
}

async function runMode(m) {
  msg.value = "";
  msgOk.value = false;
  if (!opts.systemsList().length) {
    msg.value = "请至少选择一个系统";
    return;
  }
  busy.value = true;
  try {
    await startJob(props.runId, opts.jobPayload({ type: "retrieve", mode: m }));
    emit("job-started");
    msg.value = `已提交 ${m} 任务；完成后点「刷新报告」或切到「实验」看日志`;
    msgOk.value = true;
  } catch (e) {
    msg.value = e.message;
  } finally {
    busy.value = false;
  }
}

async function runBackfill() {
  msg.value = "";
  msgOk.value = false;
  if (!opts.hasBackfillLayers.value) {
    msg.value = "请至少选择一个 Backfill 层级";
    return;
  }
  busy.value = true;
  try {
    await startJob(props.runId, opts.jobPayload({ type: "backfill" }));
    emit("job-started");
    msg.value = "已提交 TiMEM Backfill；完成后点「刷新报告」或切到「实验」看日志";
    msgOk.value = true;
  } catch (e) {
    msg.value = e.message;
  } finally {
    busy.value = false;
  }
}

watch(() => props.runId, load, { immediate: true });
watch(refreshTick, load);
watch(mode, () => {});
</script>
