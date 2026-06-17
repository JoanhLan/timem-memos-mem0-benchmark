/** Benchmark memory systems (keep in sync with adapters/registry.py). */
export const SYSTEMS = [
  { id: "timem", label: "TiMEM", badge: "badge-timem" },
  { id: "memos", label: "MemOS", badge: "badge-memos" },
  { id: "mem0", label: "Mem0", badge: "badge-mem0" },
];

export const SYSTEM_IDS = SYSTEMS.map((s) => s.id);

export function systemLabel(id) {
  return SYSTEMS.find((s) => s.id === id)?.label || id;
}

export function systemBadge(id) {
  return SYSTEMS.find((s) => s.id === id)?.badge || "badge";
}
