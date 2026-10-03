# alstack-growth

Telegram AI-channel growth engine — closed-loop pipeline that discovers, filters, and seeds AI-topic channels/groups with organic-looking engagement for promo of a target channel.

## Architecture

```
hunt → enrich → filter → pool → seed → respond
```

| Module | File | Role |
|---|---|---|
| Catalog parsers | `parse_tg_me.py`, `parse_hottg.py`, `parse_lyzem.py`, `parse_tgdr.py`, `parse_tgram.py` | scrape public TG catalogs (tg-me, hottg, lyzem, tgdr.io, tgram.io) |
| SSR catalog scrapers | `scrape_ssr_*.py` | tgstat / telemetr / telemetrio server-side-render harvest |
| Linked-group harvester | `harvest_atlas_loop.py` | expands gramgpt atlas AI-channel set into linked groups |
| Chat hunter | `chat_hunter_loop.py` | abuse-network queries → new group discovery |
| Resolver + filter | `resolve_filter.py`, `finalize.py`, `pool_filter.py` | username resolve, NSFW/anime cleanup, two-level AI-only gate (HARD_DROP → STRONG_AI → SOFT_DROP → WEAK_AI) |
| Pool merge | `merge_pool.py` | dedup + AI-gate + merge into `pool_merged.json` |
| Wave orchestrator | `wave_chain.py` | spawns N shard workers per wave, psutil-based liveness (PowerShell CIM hangs on some boxes) |
| Shard worker | `shard_worker.py` | per-session seeding with retry-safe state persistence |
| Seeding logic | `seed_alstack.py` | paired-dialog seeding; handles `direct=True` groups without `linked_id` |
| LLM responder | `responder.py` | OpenAI-compatible endpoint; generates organic replies mentioning the promo channel |
| Process scanner | `proc_scan.py` | real-python-only process census (excludes bash wrappers) |
| Ops | `_status.py`, `_proof_now.py`, `_stats2.py` | campaign status/proof snapshots |

## Data files

- `pool_merged.json` — merged AI-only pool (channels + linked groups)
- `ai_groups_new3.json` — enriched linked groups batch
- `ai_channels_enriched.json` — enriched channel set
- `addlist_*.json` — addlist catalog dumps

## Notes

- No credentials in this repo: `.session`, `.log`, `mass_state_*`, `spambot_*`, `peers.json` are gitignored.
- LLM endpoint is read from local hermes config at runtime; no keys committed.
- `wave_chain.py` uses psutil instead of PowerShell CIM (CIM deadlocks observed on Windows).
- `shard_worker.py` state writes use tmp+retry to survive transient AV/file locks.
