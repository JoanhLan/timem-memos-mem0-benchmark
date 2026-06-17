const API_BASE = "";

async function jsonFetch(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

export async function fetchHealth() {
  return jsonFetch("/api/health");
}

export async function fetchRuns() {
  const data = await jsonFetch("/api/runs");
  return data.runs || [];
}

export async function fetchRun(runId) {
  return jsonFetch(`/api/runs/${encodeURIComponent(runId)}`);
}

export async function deleteRun(runId) {
  const id = encodeURIComponent(runId);
  try {
    return await jsonFetch(`/api/runs/${id}`, { method: "DELETE" });
  } catch (err) {
    const msg = String(err.message || "");
    if (msg.includes("501") || msg.includes("405")) {
      try {
        return await jsonFetch(`/api/runs/${id}/delete`, {
          method: "POST",
          body: "{}",
        });
      } catch {
        return jsonFetch(`/api/runs/delete?run_id=${id}`);
      }
    }
    throw err;
  }
}

export async function fetchMeta() {
  return jsonFetch("/api/meta");
}

export async function fetchJob(runId) {
  return jsonFetch(`/api/runs/${encodeURIComponent(runId)}/job`);
}

export async function createRun(runId) {
  if (runId) {
    return jsonFetch("/api/runs", {
      method: "POST",
      body: JSON.stringify({ run_id: runId }),
    });
  }
  return jsonFetch("/api/runs/new");
}

export async function startJob(runId, payload) {
  return jsonFetch(`/api/runs/${encodeURIComponent(runId)}/jobs`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchDataset(runId, { use_fixture, persona_count } = {}) {
  const qs = new URLSearchParams();
  if (use_fixture != null) qs.set("use_fixture", use_fixture ? "true" : "false");
  if (persona_count != null) qs.set("persona_count", String(persona_count));
  const q = qs.toString();
  return jsonFetch(`/api/runs/${encodeURIComponent(runId)}/dataset${q ? `?${q}` : ""}`);
}

export async function fetchPersonas(useFixture, personaCount) {
  const qs = new URLSearchParams({
    use_fixture: useFixture ? "true" : "false",
    persona_count: String(personaCount),
  });
  const data = await jsonFetch(`/api/personas?${qs}`);
  return data.personas || [];
}

export async function debugSearch(payload) {
  return jsonFetch("/api/debug/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchReferenceBaselines() {
  return jsonFetch("/api/reference-baselines");
}
