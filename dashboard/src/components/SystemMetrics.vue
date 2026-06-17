<template>
  <div>
    <div style="margin-bottom: 10px">
      <span :class="['badge', badgeClass]">{{ label }}</span>
    </div>
    <div class="metric-row">
      <MetricCard v-for="m in metrics" :key="m.label" :label="m.label" :value="m.value" />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { systemBadge } from "../constants/systems";
import MetricCard from "./MetricCard.vue";
import { formatWallTime, ms, parallelEfficiency, pct, tokens } from "../utils";

const props = defineProps({
  system: { type: String, required: true },
  label: { type: String, required: true },
  ingest: { type: Object, default: null },
  retrieval: { type: Object, default: null },
});

const badgeClass = computed(() => systemBadge(props.system));

function latencyP50(block) {
  if (!block) return null;
  return block.add_latency?.p50 ?? block.latency_p50 ?? block.latency?.p50;
}

function sessionLatencyP50(block) {
  if (!block) return null;
  return block.session_latency?.p50 ?? null;
}

const metrics = computed(() => {
  const items = [];
  const ing = props.ingest;
  const ret = props.retrieval;
  if (ing) {
    items.push({
      label: "Ingest OK",
      value: `${ing.add_success_count ?? ing.success_count ?? 0}/${ing.add_count ?? ing.session_count ?? 0} adds`,
    });
    items.push({ label: "Ingest p50", value: ms(latencyP50(ing)) });
    const sessP50 = sessionLatencyP50(ing);
    if (sessP50 != null) {
      items.push({ label: "Session p50", value: ms(sessP50) });
    }
    if (ing.add_latency_estimated) {
      items.push({ label: "Add latency", value: "estimated" });
    }
    items.push({ label: "Ingest wall", value: formatWallTime(ing.run_wall_ms) });
    if (ing.sum_latency_ms != null && ing.run_wall_ms) {
      items.push({
        label: "Parallel eff.",
        value: parallelEfficiency(ing.sum_latency_ms, ing.run_wall_ms),
      });
    }
    if (ing.avg_input_tokens != null) {
      items.push({ label: "Avg in tok", value: tokens(ing.avg_input_tokens) });
    }
  }
  if (ret) {
    items.push({ label: "Recall@5", value: pct(ret.recall_at_5) });
    items.push({ label: "Recall@10", value: pct(ret.recall_at_10) });
    items.push({ label: "Judge", value: pct(ret.judge_accuracy) });
    items.push({ label: "Retr. p50", value: ms(latencyP50(ret)) });
    items.push({ label: "Retr. wall", value: formatWallTime(ret.run_wall_ms) });
    if (ret.sum_work_ms != null && ret.run_wall_ms) {
      items.push({
        label: "Parallel eff.",
        value: parallelEfficiency(ret.sum_work_ms, ret.run_wall_ms),
      });
    }
    items.push({
      label: "Avg tokens",
      value: ret.avg_recalled_tokens != null ? tokens(ret.avg_recalled_tokens) : "—",
    });
    if (ret.p50_recalled_tokens != null) {
      items.push({ label: "p50 tokens", value: tokens(ret.p50_recalled_tokens) });
    }
    if (ret.total_judge_tokens != null) {
      items.push({ label: "Judge tok", value: tokens(ret.total_judge_tokens) });
    }
    if (ret.total_judge_latency_ms != null) {
      items.push({ label: "Judge Σ", value: formatWallTime(ret.total_judge_latency_ms) });
    }
    if (ret.backfill_summary?.backfill_wall_ms != null) {
      items.push({
        label: "Backfill wall",
        value: formatWallTime(ret.backfill_summary.backfill_wall_ms),
      });
    }
    if (ret.backfill_summary?.backfill_total_ms?.p50 != null) {
      items.push({
        label: "Backfill p50",
        value: ms(ret.backfill_summary.backfill_total_ms.p50),
      });
    }
    items.push({ label: "Empty", value: String(ret.empty_count ?? 0) });
  }
  return items;
});
</script>
