<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">调试 / 单题检索</h2>
      <p class="muted">不写入 benchmark 报告，仅当场对比召回</p>
    </div>

    <div class="card card-pad">
      <div class="form-grid">
        <div class="form-group">
          <label class="form-label">Run ID</label>
          <input class="form-input" :value="runId" readonly placeholder="左侧选择 Run" />
        </div>
        <div class="form-group">
          <label class="form-label">数据集（加载 persona 列表）</label>
          <select v-model="dataset" class="form-input" @change="loadPersonas">
            <option value="fixture">Fixture</option>
            <option value="locomo">LoCoMo 10</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Persona</label>
          <select v-model="personaId" class="form-input">
            <option v-for="p in personas" :key="p.persona_id" :value="p.persona_id">
              {{ p.persona_id }}
            </option>
          </select>
        </div>
        <div class="form-group" style="grid-column: 1 / -1">
          <label class="form-label">Query</label>
          <textarea v-model="query" class="form-input" rows="2" placeholder="输入检索问题" />
        </div>
      </div>
      <div class="check-row" style="margin-bottom: 12px">
        <label v-for="sys in SYSTEMS" :key="sys.id">
          <input type="checkbox" v-model="sysEnabled[sys.id]" /> {{ sys.label }}
        </label>
      </div>
      <details v-if="sysEnabled.timem" style="margin-bottom: 12px">
        <summary class="form-label">TiMEM 检索参数</summary>
        <div class="form-grid" style="margin-top: 8px">
          <div class="form-group">
            <label class="form-label">search_mode</label>
            <select v-model="timemSearchMode" class="form-input">
              <option value="">默认</option>
              <option value="semantic">semantic</option>
              <option value="enhanced_semantic">enhanced_semantic</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">use_hybrid</label>
            <select v-model="timemUseHybrid" class="form-input">
              <option value="">默认</option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
        </div>
      </details>
      <button class="btn btn-primary" type="button" :disabled="searching || !runId" @click="search">
        多系统检索
      </button>
      <div v-if="error" class="error-box" style="margin-top: 12px">{{ error }}</div>
    </div>

    <div v-if="result" class="grid-systems" style="margin-top: 16px">
      <div v-for="sys in SYSTEMS" :key="sys.id">
        <div v-if="result.results?.[sys.id]" class="card card-pad">
          <h3>
            <span :class="['badge', sys.badge]">{{ sys.label }}</span>
            {{ ms(result.results[sys.id].latency_ms) }}
            <span v-if="result.results[sys.id].recalled_tokens != null" class="muted">
              · {{ result.results[sys.id].recalled_tokens }} tok
            </span>
          </h3>
          <MemoryList :records="mapRecords(result.results[sys.id].records)" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from "vue";
import { SYSTEMS } from "../../constants/systems";
import { debugSearch, fetchPersonas } from "../../api";
import MemoryList from "../../components/MemoryList.vue";
import { ms } from "../../utils";

const props = defineProps({ runId: { type: String, default: "" } });

const dataset = ref("fixture");
const personas = ref([]);
const personaId = ref("");
const query = ref("");
const timemSearchMode = ref("");
const timemUseHybrid = ref("");
const sysEnabled = reactive(Object.fromEntries(SYSTEMS.map((s) => [s.id, true])));
const searching = ref(false);
const error = ref("");
const result = ref(null);

function mapRecords(rows) {
  return (rows || []).map((r) => ({
    content: r.content,
    type: r.type,
    layer: r.layer,
    score: r.score,
  }));
}

async function loadPersonas() {
  const useFixture = dataset.value === "fixture";
  const count = useFixture ? 1 : 10;
  try {
    personas.value = await fetchPersonas(useFixture, count);
    if (personas.value.length) personaId.value = personas.value[0].persona_id;
  } catch (e) {
    error.value = e.message;
  }
}

async function search() {
  error.value = "";
  result.value = null;
  const systems = SYSTEMS.filter((s) => sysEnabled[s.id]).map((s) => s.id);
  if (!systems.length || !query.value.trim()) {
    error.value = "请选择系统并输入 query";
    return;
  }
  searching.value = true;
  try {
    const timem_overrides = {};
    if (timemSearchMode.value) timem_overrides.search_mode = timemSearchMode.value;
    if (timemUseHybrid.value === "true") timem_overrides.use_hybrid = true;
    if (timemUseHybrid.value === "false") timem_overrides.use_hybrid = false;
    result.value = await debugSearch({
      run_id: props.runId,
      persona_id: personaId.value,
      query: query.value.trim(),
      systems,
      timem_overrides: Object.keys(timem_overrides).length ? timem_overrides : undefined,
    });
  } catch (e) {
    error.value = e.message;
  } finally {
    searching.value = false;
  }
}

onMounted(loadPersonas);
watch(() => props.runId, () => {
  result.value = null;
});
</script>
