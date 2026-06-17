<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">写入语料</h2>
      <p class="muted">查看本 Run 将写入 TiMEM / MemOS 的对话原文与评测题（与 Ingest 结果页互补）</p>
    </div>

    <div v-if="!runId" class="card card-pad empty-hint">请先在左侧选择 Run（或新建 Run）。</div>
    <div v-else-if="loading" class="muted">加载语料…</div>
    <div v-else-if="error" class="error-box">{{ error }}</div>
    <div v-else-if="dataset">
      <div v-if="dataset.warning" class="error-box" style="margin-bottom: 12px">
        {{ dataset.warning }}
      </div>

      <div class="card card-pad dataset-meta">
        <span class="badge">{{ dataset.dataset_label === "fixture" ? "Fixture" : "LoCoMo" }}</span>
        <span class="muted">
          已加载 {{ dataset.persona_count_loaded ?? dataset.personas?.length }} /
          配置 {{ dataset.persona_count }} persona · {{ totalSessions }} sessions ·
          {{ totalQuestions }} 评测题
        </span>
        <span v-if="dataset.load_source_label" class="hint">
          数据源: {{ dataset.load_source_label }}
        </span>
      </div>

      <div class="dataset-layout">
        <aside class="dataset-side">
          <label class="form-label">Persona</label>
          <select v-model="personaId" class="form-input" @change="onPersonaChange">
            <option v-for="p in dataset.personas" :key="p.persona_id" :value="p.persona_id">
              {{ p.persona_id }}
            </option>
          </select>

          <div v-if="currentPersona" class="user-id-block">
            <div class="form-label">写入 user_id</div>
            <div class="user-id-line"><span class="badge badge-timem">TiMEM</span> {{ currentPersona.user_ids?.timem || "—" }}</div>
            <div class="user-id-line"><span class="badge badge-memos">MemOS</span> {{ currentPersona.user_ids?.memos || "—" }}</div>
          </div>

          <label class="form-label" style="margin-top: 12px">Sessions</label>
          <button
            v-for="s in currentPersona?.sessions || []"
            :key="s.session_id"
            type="button"
            :class="['session-btn', sessionId === s.session_id ? 'active' : '']"
            @click="sessionId = s.session_id"
          >
            <span class="session-id">{{ s.session_id }}</span>
            <span class="muted">{{ s.message_count }} 条</span>
          </button>
        </aside>

        <section class="dataset-main">
          <h3 class="section-title">对话内容</h3>
          <div v-if="currentSession" class="chat-thread">
            <div
              v-for="(msg, i) in currentSession.messages"
              :key="i"
              :class="['chat-bubble', msg.role === 'user' ? 'user' : 'assistant']"
            >
              <div class="chat-role">{{ msg.role === "user" ? "User" : "Assistant" }}</div>
              <div class="chat-text">{{ msg.content }}</div>
            </div>
          </div>
          <p v-else class="muted">选择左侧 session</p>

          <h3 class="section-title" style="margin-top: 20px">评测题（Retrieval 会用这些 question / gold）</h3>
          <table class="data qa-table">
            <thead>
              <tr>
                <th>Question</th>
                <th>Gold</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(qa, i) in currentPersona?.qa_pairs || []" :key="i">
                <td>{{ qa.question }}</td>
                <td><strong>{{ qa.answer }}</strong></td>
                <td>{{ qa.category || "—" }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue";
import { fetchDataset, fetchJob } from "../../api";
import { useBenchmarkOptions } from "../../composables/useBenchmarkOptions";

const props = defineProps({ runId: { type: String, default: "" } });
const refreshTick = inject("refreshTick", ref(0));
const opts = useBenchmarkOptions();

const dataset = ref(null);
const loading = ref(false);
const error = ref("");
const personaId = ref("");
const sessionId = ref("");

const currentPersona = computed(() =>
  (dataset.value?.personas || []).find((p) => p.persona_id === personaId.value)
);

const currentSession = computed(() =>
  (currentPersona.value?.sessions || []).find((s) => s.session_id === sessionId.value)
);

const totalSessions = computed(() =>
  (dataset.value?.personas || []).reduce((n, p) => n + (p.sessions?.length || 0), 0)
);

const totalQuestions = computed(() =>
  (dataset.value?.personas || []).reduce((n, p) => n + (p.qa_pairs?.length || 0), 0)
);

function onPersonaChange() {
  const sessions = currentPersona.value?.sessions || [];
  sessionId.value = sessions[0]?.session_id || "";
}

async function load() {
  if (!props.runId) {
    dataset.value = null;
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    const job = await fetchJob(props.runId).catch(() => null);
    const extra = job?.options
      ? {}
      : { use_fixture: opts.useFixture.value, persona_count: opts.personaCount.value };
    dataset.value = await fetchDataset(props.runId, extra);
    const personas = dataset.value.personas || [];
    personaId.value = personas[0]?.persona_id || "";
    onPersonaChange();
  } catch (e) {
    error.value = e.message;
    dataset.value = null;
  } finally {
    loading.value = false;
  }
}

watch(() => props.runId, load, { immediate: true });
watch(refreshTick, load);
watch([() => opts.useFixture.value, () => opts.personaCount.value], () => {
  if (props.runId) load();
});
</script>
