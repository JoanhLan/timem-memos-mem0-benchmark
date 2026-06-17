<template>
  <table class="data" v-if="rows.length">
    <thead>
      <tr>
        <th>Persona</th>
        <th>Session</th>
        <th>OK</th>
        <th>Latency</th>
        <th>Memories</th>
        <th>Error</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.session_id + row.persona_id">
        <td style="font-size: 0.82rem">{{ row.persona_id }}</td>
        <td style="font-size: 0.82rem">{{ row.session_id }}</td>
        <td>
          <span :class="row.success ? 'badge badge-ok' : 'badge badge-bad'">
            {{ row.success ? "Yes" : "No" }}
          </span>
        </td>
        <td>{{ ms(row.latency_ms) }}</td>
        <td>{{ row.memory_count ?? "—" }}</td>
        <td style="font-size: 0.75rem; color: var(--bad)">{{ row.error || "—" }}</td>
      </tr>
    </tbody>
  </table>
  <div v-else class="muted">No ingest data</div>
</template>

<script setup>
import { ms } from "../utils";

defineProps({
  rows: { type: Array, default: () => [] },
});
</script>
