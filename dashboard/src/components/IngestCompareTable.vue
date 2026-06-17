<template>
  <div class="card" style="overflow: hidden">
    <div v-if="!aligned.length" class="card-pad muted">No ingest data</div>
    <div v-else class="table-scroll-wrap">
      <table class="data data-compact ingest-compare">
        <thead>
          <tr>
            <th class="sticky-col" rowspan="2">Persona</th>
            <th class="sticky-col-2" rowspan="2">Session</th>
            <th
              v-for="sys in displaySystems"
              :key="`${sys}-group`"
              :class="['col-group', 'col-group-start', `col-group-${sys}`]"
              colspan="7"
            >
              <span :class="['badge', systemBadge(sys)]">{{ systemLabel(sys) }}</span>
            </th>
          </tr>
          <tr>
            <template v-for="sys in displaySystems" :key="`${sys}-metrics`">
              <th :class="['col-group', 'col-group-start', `col-group-${sys}`]">OK</th>
              <th :class="['col-group', `col-group-${sys}`]">Add avg</th>
              <th :class="['col-group', `col-group-${sys}`]">In tok</th>
              <th :class="['col-group', `col-group-${sys}`]">Pairs</th>
              <th :class="['col-group', `col-group-${sys}`]">API</th>
              <th :class="['col-group', `col-group-${sys}`]">Memories</th>
              <th :class="['col-group', `col-group-${sys}`]">Error</th>
            </template>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in aligned" :key="row.session_id">
            <td class="sticky-col cell-id" :title="row.persona_id">{{ row.persona_id }}</td>
            <td class="sticky-col-2 cell-id" :title="row.session_id">{{ row.session_id }}</td>
            <template v-for="sys in displaySystems" :key="`${row.session_id}-${sys}`">
              <td :class="['col-group', 'col-group-start', `col-group-${sys}`]">
                <span :class="okBadgeClass(row.systems?.[sys]?.success)">
                  {{ row.systems?.[sys]?.success ? "Yes" : row.systems?.[sys] ? "No" : "—" }}
                </span>
              </td>
              <td :class="['col-group', `col-group-${sys}`, 'num']">
                {{ ms(row.systems?.[sys]?.avg_add_latency_ms ?? addAvg(row.systems?.[sys])) }}
              </td>
              <td :class="['col-group', `col-group-${sys}`, 'num']">
                {{ tokens(row.systems?.[sys]?.input_tokens) }}
              </td>
              <td :class="['col-group', `col-group-${sys}`, 'num']">
                {{ row.systems?.[sys]?.pair_count ?? "—" }}
              </td>
              <td :class="['col-group', `col-group-${sys}`, 'num']">
                {{ row.systems?.[sys]?.api_calls ?? "—" }}
              </td>
              <td :class="['col-group', `col-group-${sys}`, 'num']">
                {{ row.systems?.[sys]?.memory_count ?? "—" }}
              </td>
              <td
                :class="['col-group', `col-group-${sys}`, 'cell-error']"
                :title="row.systems?.[sys]?.error || ''"
              >
                {{ row.systems?.[sys]?.error || "—" }}
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { SYSTEM_IDS, systemBadge, systemLabel } from "../constants/systems";
import { alignSessionsBySystem, ms, tokens } from "../utils";

const props = defineProps({
  systems: { type: Array, default: () => [...SYSTEM_IDS] },
  detailsBySystem: { type: Object, default: () => ({}) },
});

const displaySystems = computed(() => {
  const fromProps = props.systems?.length ? props.systems : SYSTEM_IDS;
  const hasData = fromProps.some((id) => (props.detailsBySystem[id] || []).length);
  if (!hasData) return fromProps;
  return fromProps.filter(
    (id) => (props.detailsBySystem[id] || []).length || fromProps.includes(id)
  );
});

const aligned = computed(() =>
  alignSessionsBySystem(props.detailsBySystem, displaySystems.value)
);

function okBadgeClass(success) {
  if (success === true) return "badge badge-ok";
  if (success === false) return "badge badge-bad";
  return "badge";
}

function addAvg(row) {
  if (!row?.latency_ms || !row?.api_calls) return null;
  return row.latency_ms / row.api_calls;
}
</script>
