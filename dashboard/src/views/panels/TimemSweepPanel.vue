<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">TiMEM 参数 Sweep</h2>
      <p class="muted">网格测试 search_mode / use_hybrid / rethink 等参数组合</p>
    </div>

    <div v-if="!runId" class="card card-pad empty-hint">请先在左侧选择或新建 Run。</div>

    <div v-else class="card card-pad">
      <RunOptionsForm :opts="opts" :show-skip-t1="false" :show-timem-advanced="true" />

      <div class="form-grid" style="margin-top: 12px">
        <div class="form-group">
          <label class="form-label">Sweep 轴（逗号分隔）</label>
          <input v-model="sweepParams" class="form-input" placeholder="search_mode,use_hybrid" />
        </div>
        <div class="form-group">
          <label class="form-label">模式</label>
          <select v-model="sweepMode" class="form-input">
            <option value="T0">T0</option>
            <option value="T1">T1（含 backfill）</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">预设</label>
          <select v-model="opts.preset.value" class="form-input">
            <option value="stable">stable</option>
            <option value="paper">paper</option>
          </select>
        </div>
      </div>

      <div class="check-row" style="margin: 12px 0">
        <label><input type="checkbox" v-model="skipBackfill" /> 跳过 backfill</label>
        <label><input type="checkbox" v-model="skipIngest" /> 跳过 ingest（复用已有数据）</label>
      </div>

      <button class="btn btn-primary" type="button" :disabled="busy" @click="startSweep">
        启动 TiMEM Sweep
      </button>
      <p v-if="message" class="error-box" style="margin-top: 12px">{{ message }}</p>
    </div>

    <div v-if="matrix.length" class="card card-pad" style="margin-top: 16px">
      <h3 style="margin-top: 0">参数矩阵</h3>
      <div class="sweep-heatmap">
        <table class="data-table">
          <thead>
            <tr>
              <th>参数</th>
              <th>Judge</th>
              <th>Recall@10</th>
              <th>Avg tokens</th>
              <th>p50 latency</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in matrix" :key="idx">
              <td><code>{{ formatParams(row.params) }}</code></td>
              <td :class="heatClass(row.metrics?.judge_accuracy)">{{ pct(row.metrics?.judge_accuracy) }}</td>
              <td>{{ pct(row.metrics?.recall_at_10) }}</td>
              <td :class="heatClassToken(row.metrics?.avg_recalled_tokens)">
                {{ tokens(row.metrics?.avg_recalled_tokens) }}
              </td>
              <td>{{ ms(row.metrics?.latency_p50) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, onMounted, ref, watch } from "vue";
import RunOptionsForm from "../../components/RunOptionsForm.vue";
import { useBenchmarkOptions } from "../../composables/useBenchmarkOptions";
import { fetchMeta, fetchRun, startJob } from "../../api";
import { ms, pct } from "../../utils";

const props = defineProps({ runId: { type: String, default: "" } });
const bumpRefresh = inject("bumpRefresh", () => {});

const opts = useBenchmarkOptions();
const sweepParams = ref("search_mode,use_hybrid");
const sweepMode = ref("T1");
const skipBackfill = ref(false);
const skipIngest = ref(false);
const busy = ref(false);
const message = ref("");
const matrix = ref([]);

function tokens(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return String(Math.round(Number(v)));
}

function formatParams(params) {
  if (!params) return "—";
  return Object.entries(params)
    .map(([k, v]) => `${k}=${v}`)
    .join(", ");
}

function heatClass(v) {
  if (v == null) return "";
  if (v >= 0.8) return "heat-high";
  if (v >= 0.5) return "heat-mid";
  return "heat-low";
}

function heatClassToken(v) {
  if (v == null) return "";
  if (v <= 600) return "heat-high";
  if (v <= 1200) return "heat-mid";
  return "heat-low";
}

async function loadMatrix() {
  if (!props.runId) return;
  try {
    const data = await fetchRun(props.runId);
    matrix.value = data.sweep_matrix?.matrix || [];
  } catch {
    matrix.value = [];
  }
}

async function startSweep() {
  message.value = "";
  busy.value = true;
  try {
    const meta = await fetchMeta();
    if (!(meta.features || []).includes("timem_sweep")) {
      message.value =
        "后端 API 版本过旧（不支持 timem_sweep）。请在终端 Ctrl+C 停掉 dashboard，再执行: python main.py dashboard --rebuild";
      return;
    }
    await startJob(
      props.runId,
      opts.jobPayload({
        type: "timem_sweep",
        mode: sweepMode.value,
        systems: ["timem"],
        sweep_params: sweepParams.value,
        skip_backfill: skipBackfill.value,
        skip_ingest: skipIngest.value,
      })
    );
    bumpRefresh();
    message.value = "Sweep 已启动，请稍后刷新查看矩阵";
  } catch (e) {
    message.value = e.message;
  } finally {
    busy.value = false;
  }
}

onMounted(loadMatrix);
watch(() => props.runId, loadMatrix);
</script>
