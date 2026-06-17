<template>
  <div class="card card-pad">
    <h3 class="section-title" style="margin-top: 0">效率对比</h3>
    <p class="muted" style="margin-bottom: 12px">
      召回 token 使用 cl100k_base 估算；参考基线需与当前 preset/top_k 对齐才可直比。
      <template v-if="presetLabel">当前 preset: <strong>{{ presetLabel }}</strong></template>
      <template v-if="topKLabel"> · top_k: <strong>{{ topKLabel }}</strong></template>
    </p>
    <table class="data-table">
      <thead>
        <tr>
          <th>系统</th>
          <th>Judge</th>
          <th>Recall@10</th>
          <th>Retr. p50</th>
          <th>Retr. wall</th>
          <th>Parallel eff.</th>
          <th>Avg tokens</th>
          <th>p50 tokens</th>
          <th>Backfill p50</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td><span :class="['badge', row.badge]">{{ row.label }}</span></td>
          <td>{{ pct(row.judge) }}</td>
          <td>{{ pct(row.recall10) }}</td>
          <td>{{ ms(row.latencyP50) }}</td>
          <td>{{ formatWallTime(row.wallMs) }}</td>
          <td>{{ row.parallelEff ?? "—" }}</td>
          <td>{{ tokens(row.avgTokens) }}</td>
          <td>{{ tokens(row.p50Tokens) }}</td>
          <td>{{ ms(row.backfillP50) }}</td>
        </tr>
        <tr v-for="ref in referenceRows" :key="ref.id" class="ref-row">
          <td><span class="badge badge-ref">{{ ref.label }}</span></td>
          <td>{{ pct(ref.judge) }}</td>
          <td>—</td>
          <td>—</td>
          <td>—</td>
          <td>{{ tokens(ref.avgTokens) }}</td>
          <td>—</td>
          <td>—</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { SYSTEMS } from "../constants/systems";
import { formatWallTime, ms, parallelEfficiency, pct, tokens } from "../utils";

const props = defineProps({
  retrieval: { type: Object, default: () => ({}) },
  referenceBaselines: { type: Object, default: () => ({}) },
});

const rows = computed(() =>
  SYSTEMS.map((sys) => {
    const block = props.retrieval?.[sys.id] || {};
    const backfill = block.backfill_summary?.backfill_total_ms || {};
    return {
      id: sys.id,
      label: sys.label,
      badge: sys.badge,
      judge: block.judge_accuracy,
      recall10: block.recall_at_10,
      latencyP50: block.latency?.p50 ?? block.latency_p50,
      wallMs: block.run_wall_ms,
      parallelEff:
        block.sum_work_ms != null && block.run_wall_ms
          ? parallelEfficiency(block.sum_work_ms, block.run_wall_ms)
          : null,
      avgTokens: block.avg_recalled_tokens,
      p50Tokens: block.p50_recalled_tokens,
      backfillP50: backfill.p50 ?? block.backfill_total_p50,
      preset: block.preset,
      topK: block.top_k,
    };
  })
);

const presetLabel = computed(() => rows.value.find((r) => r.preset)?.preset || null);
const topKLabel = computed(() => {
  const k = rows.value.find((r) => r.topK != null)?.topK;
  return k != null ? String(k) : null;
});

const referenceRows = computed(() => {
  const refs = props.referenceBaselines || {};
  return Object.entries(refs).map(([id, item]) => ({
    id,
    label: item.label || id,
    judge: item.overall_accuracy,
    avgTokens: item.avg_recalled_tokens,
  }));
});
</script>
