# Production Schema

The service schema lives in [service/schema.sql](../service/schema.sql). `service/leaderboard.example.db` is a schema-only SQLite database generated from that file. The live leaderboard database is runtime state and should not be committed.

## Tables

### `teams`

- `id`: deterministic team ID
- `name`: unique display name
- `created_at`: creation timestamp

### `users`

- `id`: deterministic user ID
- `email`: submitter identifier
- `display_name`: submitter display name
- `team_id`: owning team
- `created_at`: creation timestamp

### `submissions`

- `id`: submission UUID
- `team_id`: owning team
- `created_by_user_id`: submitting user
- `status`: `queued`, `running`, `completed`, `failed`, or `cancelled`
- `storage_key`: uploaded zip path or object-storage key
- `runtime_spec`: evaluator/runtime label; currently `nanofold-local`
- `original_filename`: uploaded filename
- `config_json`: parsed `config.yaml` snapshot
- `description`: optional config description
- `track`: competition track, usually `limited`
- `runtime_sec`: evaluation runtime
- `valid`: integer boolean
- `invalid_reason`: failure/cancel reason
- `created_at`, `started_at`, `completed_at`: lifecycle timestamps

### `scores`

- `submission_id`: scored submission
- `track`: competition track
- `foldscore_auc_hidden`: primary leaderboard score; hidden score when available, otherwise public validation score
- `final_hidden_foldscore`: hidden FoldScore when available
- `public_val_foldscore`: public validation FoldScore
- `gdt_ha_ca_auc`: GDT-HA component
- `lddt_atom14_auc`: lDDT-atom14 component
- `molprobity_clash_atom14_auc`: MolProbity Clash component
- `total_runtime_sec`: evaluation runtime
- `raw_summary_json`: raw public/hidden score payload

### `submission_targets`

Reserved for per-target details when target-level persistence is enabled.

- `submission_id`
- `target_id`

## Leaderboard Logic

`GET /leaderboard` returns scored submissions ordered by:

1. `foldscore_auc_hidden` descending
2. `total_runtime_sec` ascending

The UI also separates queued/running submissions and failed/cancelled submissions for review.
