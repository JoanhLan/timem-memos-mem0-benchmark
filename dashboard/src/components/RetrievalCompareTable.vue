<template>
  <div>
    <div class="card" style="overflow: hidden; margin-bottom: 16px">
      <div class="table-scroll-wrap">
        <table class="data data-compact retrieval-compare">
        <thead>
          <tr>
            <th class="sticky-col cell-question">Question</th>
            <th class="sticky-col-2 cell-gold">Gold</th>
            <th v-for="sys in displaySystems" :key="`${sys}-r5`">{{ systemLabel(sys) }} R@5</th>
            <th v-for="sys in displaySystems" :key="`${sys}-r10`">{{ systemLabel(sys) }} R@10</th>
            <th v-for="sys in displaySystems" :key="`${sys}-tok`">{{ systemLabel(sys) }} Tok</th>
            <th v-for="sys in displaySystems" :key="`${sys}-judge`">{{ systemLabel(sys) }} Judge</th>
            <th v-for="sys in displaySystems" :key="`${sys}-ms`">{{ systemLabel(sys) }} ms</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in aligned"
            :key="idx"
            :class="['clickable', selectedIdx === idx ? 'selected' : '']"
            @click="selectedIdx = idx"
          >
            <td class="sticky-col cell-question" :title="row.question">{{ row.question }}</td>
            <td class="sticky-col-2 cell-gold"><strong>{{ row.gold }}</strong></td>
            <td v-for="sys in displaySystems" :key="`${sys}-r5v`">
              <span :class="badgeClass(row.systems?.[sys]?.['recall@5'])">
                {{ pct(row.systems?.[sys]?.["recall@5"]) }}
              </span>
            </td>
            <td v-for="sys in displaySystems" :key="`${sys}-r10v`">
              <span :class="badgeClass(row.systems?.[sys]?.['recall@10'])">
                {{ pct(row.systems?.[sys]?.["recall@10"]) }}
              </span>
            </td>
            <td
              v-for="sys in displaySystems"
              :key="`${sys}-tokv`"
              :class="heatClassToken(row.systems?.[sys]?.recalled_tokens)"
            >
              {{ tokens(row.systems?.[sys]?.recalled_tokens) }}
            </td>
            <td v-for="sys in displaySystems" :key="`${sys}-jv`">
              <span :class="badgeClass(row.systems?.[sys]?.judge?.can_answer ? 1 : 0)">
                {{ row.systems?.[sys]?.judge?.can_answer ? "Yes" : "No" }}
              </span>
            </td>
            <td v-for="sys in displaySystems" :key="`${sys}-msv`">
              {{ ms(row.systems?.[sys]?.latency_ms) }}
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <div v-if="selectedRow" class="compare-panel">
      <h3>{{ selectedRow.question }}</h3>
      <div class="compare-cols grid-systems">
        <div
          v-for="sys in displaySystems"
          :key="sys"
          :class="['compare-col', sys]"
        >
          <div style="margin-bottom: 8px">
            <span :class="['badge', systemBadge(sys)]">{{ systemLabel(sys) }}</span>
            <span class="muted">
              · {{ selectedRow.systems?.[sys]?.result_count ?? 0 }} results
              · {{ tokens(selectedRow.systems?.[sys]?.recalled_tokens) }} tok
            </span>
          </div>
          <div v-if="layerBar(selectedRow.systems?.[sys]?.layer_breakdown)" class="layer-bar muted" style="margin-bottom: 8px; font-size: 12px">
            {{ layerBar(selectedRow.systems?.[sys]?.layer_breakdown) }}
          </div>
          <MemoryList
            :records="selectedRow.systems?.[sys]?.records"
            :gold="selectedRow.gold"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { SYSTEM_IDS, systemBadge, systemLabel } from "../constants/systems";
import MemoryList from "./MemoryList.vue";
import { alignQuestionsBySystem, heatClassToken, ms, pct, tokens } from "../utils";

const props = defineProps({
  systems: { type: Array, default: () => [...SYSTEM_IDS] },
  detailsBySystem: { type: Object, default: () => ({}) },
  timemDetails: { type: Array, default: () => [] },
  memosDetails: { type: Array, default: () => [] },
});

const selectedIdx = ref(0);

const mergedDetails = computed(() => {
  if (props.detailsBySystem && Object.keys(props.detailsBySystem).length) {
    return props.detailsBySystem;
  }
  return {
    timem: props.timemDetails,
    memos: props.memosDetails,
  };
});

const displaySystems = computed(() => {
  const fromProps = props.systems?.length ? props.systems : SYSTEM_IDS;
  return fromProps.filter((id) => {
    const rows = mergedDetails.value[id];
    return rows && rows.length;
  }).length
    ? fromProps.filter((id) => (mergedDetails.value[id] || []).length || fromProps.includes(id))
    : fromProps;
});

const aligned = computed(() =>
  alignQuestionsBySystem(mergedDetails.value, displaySystems.value)
);

const selectedRow = computed(() => aligned.value[selectedIdx.value] || null);

function badgeClass(v) {
  if (v == null) return "badge";
  const n = Number(v);
  if (n >= 1 || v === true) return "badge badge-ok";
  if (n <= 0 || v === false) return "badge badge-bad";
  return "badge badge-warn";
}

function layerBar(breakdown) {
  if (!breakdown || typeof breakdown !== "object") return "";
  const parts = Object.entries(breakdown)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => `${k}:${v}`);
  return parts.length ? parts.join(" · ") : "";
}

watch(
  () => [mergedDetails.value, props.systems],
  () => {
    selectedIdx.value = 0;
  },
  { deep: true }
);
</script>

<style scoped>
tr.selected td {
  background: #eff6ff !important;
}

tr.selected td.sticky-col,
tr.selected td.sticky-col-2 {
  background: #eff6ff !important;
}
</style>
