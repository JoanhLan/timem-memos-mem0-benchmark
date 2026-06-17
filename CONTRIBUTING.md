# Contributing

Thanks for your interest in improving this benchmark harness.

## Development setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt -r requirements-dev.txt
```

## Running tests

Unit tests mock external APIs — no API keys required:

```bash
pytest tests/unit -q
```

## Pull requests

1. Fork the repository and create a feature branch.
2. Keep changes focused; match existing code style and naming.
3. Run `pytest tests/unit -q` before opening a PR.
4. If you change ingest granularity, concurrency, session IDs, or scoring rules, update [BENCHMARK_PROTOCOL.md](./BENCHMARK_PROTOCOL.md) in the same PR.

## Reporting issues

- Do **not** paste API keys or `.env` contents in issues.
- Include `run_id`, command used, and relevant snippets from `reports/{run_id}/job.log` when reporting benchmark failures.
