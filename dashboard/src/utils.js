import { SYSTEM_IDS } from "./constants/systems";

export function pct(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(Number(v) * 100).toFixed(1)}%`;
}

export function ms(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${Math.round(Number(v))} ms`;
}

/** Human-readable duration from milliseconds (e.g. 774000 → "12m 54s"). */
export function formatWallTime(msVal) {
  if (msVal == null || Number.isNaN(msVal)) return "—";
  const totalSec = Math.round(Number(msVal) / 1000);
  if (totalSec < 60) return `${totalSec}s`;
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  if (min < 60) return sec ? `${min}m ${sec}s` : `${min}m`;
  const hr = Math.floor(min / 60);
  const remMin = min % 60;
  return remMin ? `${hr}h ${remMin}m` : `${hr}h`;
}

export function tokens(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${Math.round(Number(v))}`;
}

/** Lower token count = greener (more efficient). */
export function heatClassToken(v) {
  if (v == null || Number.isNaN(v)) return "";
  const n = Number(v);
  if (n <= 600) return "heat-high";
  if (n <= 1200) return "heat-mid";
  return "heat-low";
}

export function parallelEfficiency(sumMs, wallMs) {
  if (!sumMs || !wallMs || wallMs <= 0) return "—";
  return `${(Number(sumMs) / Number(wallMs)).toFixed(1)}×`;
}

export function num(v, digits = 2) {
  if (v == null || Number.isNaN(v)) return "—";
  return Number(v).toFixed(digits);
}

export function highlightGold(text, gold) {
  if (!text || !gold) return escapeHtml(text || "");
  const tokens = gold
    .split(/[\s,;/]+/)
    .map((t) => t.trim())
    .filter((t) => t.length > 1);
  let out = escapeHtml(text);
  for (const tok of tokens) {
    const re = new RegExp(`(${escapeRegExp(tok)})`, "gi");
    out = out.replace(re, '<mark class="gold">$1</mark>');
  }
  return out;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Align retrieval details across N systems by question text. */
export function alignQuestionsBySystem(detailsBySystem = {}, systems = SYSTEM_IDS) {
  const map = new Map();
  for (const sys of systems) {
    const rows = detailsBySystem[sys] || [];
    for (const row of rows) {
      const key = row.question;
      if (!map.has(key)) {
        map.set(key, {
          question: key,
          gold: row.gold,
          persona_id: row.persona_id,
          systems: {},
        });
      }
      const entry = map.get(key);
      entry.systems[sys] = row;
      entry.gold = row.gold ?? entry.gold;
      entry.persona_id = row.persona_id ?? entry.persona_id;
    }
  }
  return [...map.values()];
}

/** Align ingest details across N systems by session_id. */
export function alignSessionsBySystem(detailsBySystem = {}, systems = SYSTEM_IDS) {
  const map = new Map();
  for (const sys of systems) {
    const rows = detailsBySystem[sys] || [];
    for (const row of rows) {
      const key = row.session_id;
      if (!key) continue;
      if (!map.has(key)) {
        map.set(key, {
          persona_id: row.persona_id,
          session_id: key,
          systems: {},
        });
      }
      const entry = map.get(key);
      entry.systems[sys] = row;
      entry.persona_id = row.persona_id ?? entry.persona_id;
    }
  }
  return [...map.values()].sort((a, b) => {
    const pc = (a.persona_id || "").localeCompare(b.persona_id || "");
    if (pc !== 0) return pc;
    return (a.session_id || "").localeCompare(b.session_id || "");
  });
}

/** @deprecated use alignQuestionsBySystem */
export function alignQuestions(timemDetails = [], memosDetails = []) {
  return alignQuestionsBySystem(
    { timem: timemDetails, memos: memosDetails },
    ["timem", "memos"]
  ).map((row) => ({
    question: row.question,
    gold: row.gold,
    persona_id: row.persona_id,
    timem: row.systems.timem || null,
    memos: row.systems.memos || null,
  }));
}

export function hasEmptyRecords(records) {
  return (records || []).some((r) => !(r.content || "").trim());
}

export function activeSystemsFromReport(reportBlock, systems = SYSTEM_IDS) {
  if (!reportBlock) return systems;
  return systems.filter((id) => reportBlock[id] != null);
}
