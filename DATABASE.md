# Database

Aloxa uses **SQLite 3** as its only persistence engine. There is no server process — every database is a single local file accessed through Python's stdlib `sqlite3` driver. Both files live under `data/` (gitignored) and are created on first run; nothing needs to be configured before the app starts.

## Hosting

| Database | File path | Created by | Purpose |
|---|---|---|---|
| Operational store | `data/aloxa.db` | `database/db.py::init_db()` on app start | Medications, schedules, intake log |
| Health RAG index | `data/health_index.db` | `scripts/build_health_index.py` (offline) | NHS knowledge chunks + vector embeddings for health Q&A |

Both paths are resolved from `config.py` (`DB_PATH`, `HEALTH_INDEX_PATH`) so no path is hardcoded elsewhere. The connection helper `database/db.py::get_connection()` (`db.py:7`) is the single chokepoint for the operational database — it sets `row_factory = sqlite3.Row` for dict-style access and enables `PRAGMA foreign_keys = ON` so the FK cascades in the schema actually fire.

The `health_index.db` file uses the `sqlite-vec` loadable extension for cosine nearest-neighbour search (`llm/health_retriever.py:54`). The extension is loaded per-connection — the file itself is still a plain SQLite database.

---

## `data/aloxa.db` — Operational store

Defined in `database/schema.sql`. Late-added columns are applied in-place by `database/db.py::_migrate()` for older DBs that predate them.

### Entity: `medications`

A registered medication the user takes. One row per drug, regardless of how many times per day it is scheduled.

| Field | Type | Justification |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Stable surrogate key. Used as the FK target by `medication_times` and `intake_log`, so it must outlive renames of the human-facing `name` field. |
| `name` | `TEXT NOT NULL` | Display name spoken back by TTS and matched against LLM `[TAKEN: ...]` tags. Free text rather than a code because users speak the brand they actually have. |
| `dosage` | `TEXT NOT NULL` | Free-form (`"500mg"`, `"1 tablet"`, `"5ml"`) — units and forms vary across drugs, so a structured numeric column would over-constrain. Always shown alongside `name` in alerts. |
| `information` | `TEXT` | Optional free-text notes (e.g. *"with food"*). Nullable because most entries don't need it; populated only when the user provides extra context. |
| `container` | `TEXT NOT NULL DEFAULT 'A' CHECK (container IN ('A', 'B'))` | Maps the medication to one of the two physical compartments on the dispenser. The `CHECK` constraint enforces hardware reality — there are only two compartments — and `manager.add_medication` re-validates at the application layer (`manager.py:17`). Defaults to `'A'` so the migration of older rows succeeds without manual intervention. |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | Audit-only — useful when debugging "why does this med exist?" Never read by application code. |

### Entity: `medication_times`

A scheduled time of day for a medication. Separate table because one medication can have many reminders per day (e.g. 08:00 and 22:00).

| Field | Type | Justification |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Surrogate key — needed because `(medication_id, scheduled_time)` is logically unique but the table is rewritten wholesale on schedule edits, so a stable row identity matters less than a simple PK. |
| `medication_id` | `INTEGER NOT NULL` + `FOREIGN KEY ... ON DELETE CASCADE` | Links back to `medications`. Cascade ensures that deleting a medication wipes its schedule in one statement, keeping the data consistent without application-layer cleanup. |
| `scheduled_time` | `TEXT NOT NULL` (`"HH:MM"` 24-hour) | Stored as text rather than `TIME` because SQLite has no real `TIME` type and string comparison on `"HH:MM"` is already chronologically correct. Also matches the format used in `intake_log.scheduled_time` for direct comparison without conversion. |

`MedicationManager.update_medication` deletes all rows for the affected `medication_id` and re-inserts them rather than diffing — simpler, atomic within one transaction, and time-edits are infrequent enough that the cost is irrelevant (`manager.py:92-100`).

### Entity: `intake_log`

One row per fired reminder — the operational record of what was due, what the user did, and how many alerts have been sent. This is the only entity with a state machine.

| Field | Type | Justification |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Used by `mark_taken(log_id)` / `mark_missed(log_id)` to address the exact reminder being responded to, even when there are multiple pending entries for the same medication. |
| `medication_id` | `INTEGER NOT NULL` + `ON DELETE CASCADE` | Joins back to the medication for display (`name`, `dosage`). Cascade prevents orphaned log rows after a medication is deleted. |
| `scheduled_time` | `TEXT NOT NULL` (`"HH:MM"`) | Denormalised copy of the time that fired this reminder. Kept on the row so reports and history queries don't need to reconstruct which `medication_times` row was active at the time, and so the log remains meaningful even if the schedule is later edited. |
| `status` | `TEXT NOT NULL DEFAULT 'pending'` | The state machine: `pending → taken` (user confirmed) or `pending → missed` (timed out after `MISSED_TIMEOUT_SECONDS`). Stored as a label rather than an int because SQL queries like `WHERE status = 'pending'` are self-documenting. |
| `reminded_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` | When the row was created (i.e. when the scheduler first noticed the reminder was due). Used by `expire_stale_reminders` to compute the missed cutoff, and by `has_reminder_today` to check if today's row already exists (`manager.py:208-218`). |
| `responded_at` | `TIMESTAMP` (nullable) | Set only when `status` leaves `pending`. Nullability is intentional — the absence of a value is itself meaningful: the reminder is still active. |
| `alert_count` | `INTEGER NOT NULL DEFAULT 0` | How many times the scheduler has alerted for this row (initial + repeats). Drives the `INITIAL` vs `REPEAT #n` label in `default_alert` (`scheduler.py:11-17`) and lets repeat-alert pacing survive process restarts. |
| `last_alerted_at` | `TIMESTAMP` (nullable) | Timestamp of the most recent alert. Combined with `REMINDER_REPEAT_DELAY_SECONDS`, it controls when the next repeat fires (`manager.py:259`). Nullable because a row is created before its first alert is ever emitted. |

The split between `reminded_at` (row creation) and `last_alerted_at` (most recent alert) lets the scheduler distinguish "this reminder is overdue" from "this reminder was just re-announced", which is what enables polite re-prompting without re-creating rows.

### Cross-cutting choices

- **Foreign keys are enabled at every connection** (`PRAGMA foreign_keys = ON` in `get_connection()`); without that, SQLite ignores `FOREIGN KEY` clauses silently. The `ON DELETE CASCADE` rules on `medication_times` and `intake_log` are the reason a single `DELETE FROM medications WHERE id = ?` cleans up everything.
- **No app-level user table.** Aloxa is a single-user device — adding a `users` table would carry no information.
- **Times as `TEXT`.** Both `scheduled_time` columns hold `"HH:MM"` strings. Lexicographic ordering equals chronological ordering for that format, so SQL comparisons (`il.scheduled_time <= ?`, `manager.py:258`) work without any date-math.
- **Migrations are forward-only and idempotent.** `_migrate` checks `PRAGMA table_info(...)` and adds missing columns with safe defaults (`db.py:28-41`); there is no version table because the migration set is small and self-checking.

---

## `data/health_index.db` — Health RAG index

A separate SQLite file, built offline by `scripts/build_health_index.py` from the markdown corpus under `data/health_corpus/`. Read at runtime by `HealthRetriever` (`llm/health_retriever.py`). Rebuilt — not migrated — when the corpus or embedding model changes; the build script `unlink()`s the old file first (`build_health_index.py:157`).

### Entity: `meta`

Free-form key/value table recording how the index was built. Lets the retriever (or a future tool) sanity-check that the runtime model matches the build-time model without rebuilding.

| Field | Type | Justification |
|---|---|---|
| `key` | `TEXT PRIMARY KEY` | Known keys: `embed_model`, `embed_dim`, `chunk_max_chars`, `chunk_count`. PK enforces no duplicates. |
| `value` | `TEXT NOT NULL` | All values stringified — keeps the table generic; numeric values are parsed by callers. |

### Entity: `chunks`

One row per text chunk extracted from the corpus. Holds the human-readable payload returned to the LLM as RAG context.

| Field | Type | Justification |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Joins to `vec_chunks.rowid` (1-to-1). Must match exactly because the vector table addresses chunks by `rowid`. |
| `title` | `TEXT NOT NULL` | The source document's title (from YAML frontmatter or filename). Surfaced to the user in citations. |
| `source` | `TEXT NOT NULL` | Origin URL or label (e.g. NHS page reference). Lets responses cite the source. |
| `section` | `TEXT NOT NULL` | The H2 heading the chunk came from. Stored explicitly so chunks never straddle section boundaries (`build_health_index.py:79-81`) and so retrieved chunks can be displayed with their context. |
| `text` | `TEXT NOT NULL` | The chunk body itself — what gets injected into the WatsonX prompt as REFERENCE INFORMATION. |

### Entity: `vec_chunks` (virtual table, `vec0` extension)

The vector index. Created via `CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[384])` (dim is read from `HEALTH_EMBED_DIM`).

| Field | Type | Justification |
|---|---|---|
| `rowid` | (implicit) | Set explicitly to match `chunks.id` so a single `JOIN chunks ON chunks.id = vec_chunks.rowid` (`health_retriever.py:80`) returns both vector and payload in one query. |
| `embedding` | `float[384]` | Sentence-transformer embedding (default `all-MiniLM-L6-v2`, 384 dims). Stored normalised so the squared L2 distance returned by sqlite-vec is convertible to cosine similarity via `cos = 1 - distance / 2` (`health_retriever.py:91`). The fixed dimension is enforced by the build script — a model whose output dim differs from `HEALTH_EMBED_DIM` raises a hard error (`build_health_index.py:126-130`). |

### Why a separate file?

- **Lifecycle.** Operational data accumulates over the user's lifetime; the RAG index is a derived artefact rebuilt from scratch when the corpus changes. Keeping them apart means rebuilding the index never risks the user's medication history.
- **Extension scope.** Only the retriever needs `sqlite-vec` loaded. Isolating it to one connection keeps the rest of the app on stock SQLite.
- **Backups.** `data/aloxa.db` is the only file that needs backing up — `health_index.db` can always be regenerated with `python3 scripts/build_health_index.py`.
