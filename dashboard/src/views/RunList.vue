<template>
  <div>
    <div class="toolbar">
      <h2 class="section-title" style="margin: 0">Benchmark runs</h2>
      <span class="muted" v-if="!loading">{{ runs.length }} run(s)</span>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>
    <div v-else-if="loading" class="card card-pad muted">Loading…</div>
    <div v-else-if="!runs.length" class="card card-pad empty-hint">
      No reports yet. Run:
      <code>python main.py ingest</code>
      then
      <code>python main.py retrieve &lt;run_id&gt;</code>
    </div>
    <div v-else class="card" style="overflow: hidden">
      <table class="data">
        <thead>
          <tr>
            <th>Run ID</th>
            <th>Modes</th>
            <template v-for="sys in SYSTEMS" :key="sys.id">
              <th>{{ sys.label }} Recall@5</th>
              <th>{{ sys.label }} Judge</th>
              <th>{{ sys.label }} Retr. p50</th>
            </template>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="run in runs"
            :key="run.run_id"
            class="clickable"
            @click="$router.push(`/runs/${run.run_id}`)"
          >
            <td>
              <strong>{{ run.run_id }}</strong>
            </td>
            <td>{{ (run.retrieval_modes || []).join(", ") || "—" }}</td>
            <template v-for="sys in SYSTEMS" :key="`${run.run_id}-${sys.id}`">
              <td>{{ pct(firstRetrieval(run, sys.id)?.recall_at_5) }}</td>
              <td>{{ pct(firstRetrieval(run, sys.id)?.judge_accuracy) }}</td>
              <td>{{ ms(firstRetrieval(run, sys.id)?.latency_p50) }}</td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { SYSTEMS } from "../constants/systems";
import { fetchRuns } from "../api";
import { ms, pct } from "../utils";

const runs = ref([]);
const loading = ref(true);
const error = ref("");

function firstRetrieval(run, system) {
  const modes = run.retrieval_modes || [];
  const mode = modes[0];
  if (!mode) return null;
  return run[system]?.retrieval?.[mode] ?? null;
}

onMounted(async () => {
  try {
    runs.value = await fetchRuns();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});
</script>
