# Deployment

How `mythoscope.io` runs: a single box, native Caddy terminating TLS in front of
a systemd-managed `mytho server` on loopback. Weights (`outputs/`) are built
elsewhere — on a GPU machine, see [embeddings-gpu-howto.md](embeddings-gpu-howto.md) —
and pushed here as data, independently of code.

Everything is driven from `fabfile.py` in the repo root over plain SSH. There is
no CI/CD, no registry, no object storage.

---

## 1. Topology

```
        :443                    :8000 (loopback only)
  ──────────────►  Caddy  ─────────────────────►  mytho server (uvicorn, 1 worker)
   TLS, ACME,      │                               │
   compression     │                               ├─ reads  /srv/mythoscope/outputs/
                   └─ /etc/caddy/Caddyfile         └─ writes /srv/mythoscope/outputs/logs/
```

Server layout — code, data and environment are **siblings, never nested**, so
`rsync --delete` into the app dir cannot reach the 368MB store or the installed
venv:

```
/srv/mythoscope/
  app/            code (rsync target); app/outputs is a symlink to ../outputs
  outputs/        the store: corpus, embeddings (ChromaDB), projections, graphs, motifs
  outputs.prev/   previous store, kept for one-command rollback
  venv/           UV_PROJECT_ENVIRONMENT — outside the project dir on purpose
/opt/mythoscope-python/         uv-managed CPython, if the box has no 3.13 (§3)
/etc/mythoscope/env             service env (root:mythoscope 0640, never rsynced)
/etc/systemd/system/mythoscope.service
/etc/caddy/Caddyfile
```

Templates for the last three live in [`etc/`](../etc/) in the repo and are
installed by `fab bootstrap`.

### Accounts

Three identities, and they are not interchangeable:

| account | used by | notes |
|---|---|---|
| `root` | `bootstrap`, and nothing else | creates the other two; nothing in `bootstrap` needs sudo |
| `ubuntu` | every other task | owns `/srv/mythoscope`, so rsync and `uv sync` run unprivileged |
| `mythoscope` | the service | `--system --no-create-home --shell nologin`; reads the tree via the group |

`bootstrap` creates `ubuntu` when the image ships root only (Hetzner,
DigitalOcean et al.), copying `/root/.ssh/authorized_keys` so the key you
bootstrapped with also drives `deploy`. It is granted `ALL=(ALL) NOPASSWD:ALL`
in `/etc/sudoers.d/mythoscope-deploy` — cloud-init's shape, so a
provider-supplied `ubuntu` and a bootstrap-created one end up identical. No
password is ever set on it: the account is key-only, and `NOPASSWD` means `sudo`
never needs one.

Ownership under `/srv/mythoscope` is `ubuntu:mythoscope` with directories `2775`
(setgid) — the service reads via the group and writes `outputs/logs` via the
setgid bit.

**`rsync -a` fights this, and wins unless you undo it.** It imposes the
*source*'s group and modes on the destination: it strips the setgid bit off the
target directory itself and lands every file in `ubuntu`'s own group, which drops
the service onto the "other" bits. Reads then happen to keep working through
`o+r`, so nothing looks wrong until Chroma tries to open its store (§5).

The source's modes are not trustworthy either — the store is built on another
machine, and one file arriving `0600` is enough to 500 whichever route reads it
(`outputs/corpus/corpus.json` did exactly that; every sibling was `0644`).

So both `deploy` and `push-outputs` end their sync with the same three passes:

| pass | why |
|---|---|
| `chgrp -Rh mythoscope` | rsync put it in the deploy user's group |
| `chmod -R g+rX` | the source may ship modes the group cannot read |
| `find -type d -exec chmod 2775` | setgid + group write, for what the service writes |

`g+rX` grants the group only what "other" or the owner already had, and adds
execute solely where something already has it — a `0600` file becomes `0640`, not
world-readable. A delta rsync re-breaks all three, so they run on every sync
rather than once at bootstrap.

Fabric falls back to your **local** username when the host's `ssh_config` block
names no `User`, which would silently deploy as a user the server has never
heard of. So the login account is always explicit on the command line, and every
task asserts the one it needs before it connects. Override the deploy account
with `MYTHO_DEPLOY_USER`.

### Configuration

`/etc/mythoscope/env` is the whole of it — installed from
[`etc/mythoscope.env.example`](../etc/mythoscope.env.example) by `bootstrap`,
and only when absent, so a server-side edit survives a re-run. It holds five
keys, and **none of them currently overrides anything**:

| key | value | `settings.py` default |
|---|---|---|
| `MYTHO_SERVER__HOST` | `127.0.0.1` | `127.0.0.1` |
| `MYTHO_SERVER__PORT` | `8000` | `8000` |
| `MYTHO_LOG_LEVEL` | `INFO` | `INFO` |
| `MYTHO_LOGS_MAX_FILES` | `20` | `20` |
| `MYTHO_SERVER__TEXT_SEARCH` | `false` | `False` |

They are there to pin, not to change. `HOST` and `PORT` are the loopback-only
invariant that makes Caddy the sole entry point, and `TEXT_SEARCH=false` matches
the torch-free `viewer` extra; a future default flip in `settings.py` must not be
able to move any of the three. `LOG_LEVEL` and `LOGS_MAX_FILES` are ordinary
knobs, in the file so you can turn logging up with a restart instead of a deploy.

Everything else is deliberately absent. Paths (`config_dir`, `outputs_*`,
`web_root`) are relative and resolved from `WorkingDirectory` — setting them here
would break the layout, not configure it. No API keys: the viewer makes no LLM
calls, and the other environment variables the code reads (`MYTHO_OFFLINE`,
`MAPSOFMYTHS_AUTH`, the per-provider keys in `model_registry.py`) are all
build-side.

Precedence is unambiguous: `settings.py` calls `load_dotenv(override=False)` and
pydantic-settings ranks real environment variables above `env_file`, so systemd's
`EnvironmentFile` wins. No `.env` reaches the server regardless — it is
gitignored, and rsync filters on `.gitignore`.

---

## 2. Commands

```bash
fab -H root@mythoscope.io bootstrap              # once per server
fab -H ubuntu@mythoscope.io deploy               # code — seconds
fab -H ubuntu@mythoscope.io push-outputs         # data — minutes, ~2s downtime
fab -H ubuntu@mythoscope.io push-outputs --from-zip=mythoscope-export-20260803.zip
fab -H ubuntu@mythoscope.io rollback-outputs     # swap outputs.prev back in
fab -H ubuntu@mythoscope.io status | logs | restart | smoke
```

The host is the site's own domain, which has to resolve to the box before
`bootstrap` anyway (Caddy needs it for the certificate); pass the IP instead
while DNS is still propagating, or add a `~/.ssh/config` alias if the box needs
a non-default key or port. The account is given on the command line rather than
in an alias because it differs per task — see Accounts above. Set
`MYTHO_DEPLOY_DOMAIN` if the site is not `mythoscope.io`.

Fabric is a *tool* here, not a dependency of the project: `fabfile.py` imports
`fabric`, `invoke` and stdlib, nothing from `src/`. So install it once, outside
the project, and `fab` works from the repo root with no venv activated:

```bash
uv tool install fabric        # `fab` lands in ~/.local/bin
```

`uv run --extra deploy fab …` is the alternative — it pins Fabric through
`uv.lock` instead of tracking latest, at the cost of naming the extra on every
call and re-checking the project venv each time.

### `bootstrap`

Idempotent; safe to re-run. Targets Debian/Ubuntu — it assumes `apt`, Caddy's
cloudsmith repo, `useradd` and `/usr/sbin/nologin`. Creates the `ubuntu` deploy
account and its sudoers drop-in; installs apt packages, Caddy (official
cloudsmith repo), and `uv` system-wide to `/usr/local/bin`; creates the
`mythoscope` system account; creates the directory tree; installs the env file,
systemd unit and Caddyfile; validates the Caddyfile before reloading Caddy.
Runs entirely as root, so it never prompts.

Running as root is also why it re-chowns `/var/log/caddy` to `caddy:caddy` right
after validating. `caddy validate` provisions the config rather than just parsing
it, so it opens the log writer — as root, creating a root-owned
`mythoscope.log`. Caddy itself runs as `caddy`, and would then fail to start with
`setting up custom log 'log0'`. The chown must come after the validate, not
before.

It refuses to run if `/root/.ssh/authorized_keys` is empty and the deploy
account does not already exist — otherwise it would create an account with no
way to log in and leave you unable to `deploy`.

It leaves the service **enabled but not started**: there is no code yet.

Point the domain's A record at the box before this runs, or Caddy cannot issue a
certificate on first request.

### `deploy`

rsync → symlink data → `uv sync --frozen --no-dev --extra viewer` → regroup
(§1) → restart → smoke check. Writes the deployed revision to `app/DEPLOYED`.
The regroup runs last so it covers what `uv sync` and the stamp wrote, not just
what rsync did.

rsync reuses the repo's own ignore rules via `--filter=':- .gitignore'`, so
there is no second ignore list to drift. Verified by dry run: 185 entries ship;
`outputs/`, `.venv/`, `.env`, `.git/`, `*.pyc` and `*.egg-info` are excluded;
`config/`, `src/server/web/`, `uv.lock`, `.python-version` and `pyproject.toml`
are included. `docs/`, `mockups/` and `tests/` are excluded explicitly.

It warns (but does not block) on a dirty working tree or an untracked `uv.lock`
— rsync will happily ship uncommitted work, which is useful while iterating and
a hazard otherwise, so `DEPLOYED` records `<sha>` or `<sha>-dirty`.

### `push-outputs`

ChromaDB holds its SQLite file and HNSW index open while serving, so the store
is swapped, never written in place.

```
                          outputs       outputs.next   outputs.prev
                       (live, serving)    (staging)     (rollback)
  ──────────────────────────────────────────────────────────────────
  before                    368M             —            368M      ← last push
  cp -a outputs next        368M      ①     368M          368M      ← peak 1.1G
  rsync src/ → next         368M      ②     368M+Δ        368M
  ── stop ── 0.23s ─────────────────────────────────────────────────┐
  sudo rm -rf prev          368M           368M             —       │
  mv outputs prev             —            368M           368M      │  ~2s
  mv next outputs           368M             —            368M      │  down
  mkdir logs, chmod 2775    368M             —            368M      │
  ── start ── 1.70s ────────────────────────────────────────────────┘
  smoke                     368M             —            368M
```

Only ① and ② move bytes; ① trades local I/O for network so that ② is a delta.
Between ② and the stop, the staged `embeddings/` is chmodded group-writable —
metadata only, and outside the window on purpose (§5 explains why the store
needs it). Everything inside the stopped window is metadata too — two
`rename(2)`s and 181 unlinks, 0.06s measured — so the ~2s is almost entirely the
Python process restarting, and downtime does not grow with the store.

Peak disk is 3× the store (space, not I/O) because the last push's
`outputs.prev` survives until the stop; moving `rm -rf prev` above the copy
would cap it at 2×. The `mkdir`/`chmod` is there because `setup_logging()`
opens a FileHandler under `outputs/logs` on every start.

If anything inside the stopped window fails, the service is started again before
the error surfaces — a swap that dies half-way should cost you the push, not the
site. The `&&` chain means a failed `rm` leaves the live store untouched, so the
restart serves the old data.

All three paths must share a filesystem — `rename(2)` cannot cross mounts, and a
mountpoint cannot be renamed at all. Mount a data volume at `/srv/mythoscope`,
never at `/srv/mythoscope/outputs`.

Excluded from the upload: `logs/` (server-local), `extraction_cache.jsonl`,
`summaries.jsonl`, `motifs/raw/` — all rebuild fuel, useless on the target.

**Folder vs `--from-zip`.** The local `outputs/` folder is the default; the zip
path exists because weights arrive as `mytho export` bundles over mail/Drive.

| | local `outputs/` | `--from-zip` |
|---|---|---|
| Provenance | none — whatever the tree holds | immutable named artifact |
| Local tree | must *be* the intended state | untouched; safe mid-experiment |
| Extra checks | none | `mytho export` warns on orphans, records the chromadb version |
| Transfer | delta | delta (staging is seeded first) |
| Cost | none | ~370MB temp disk, unpack step |

Use `--from-zip` when the weights came from someone else's GPU run; use the
folder when you built them locally and want the delta.

### The smoke check

Runs after every `deploy`, `push-outputs`, `rollback-outputs` and `restart`, over
loopback rather than through Caddy so a failure points at the service and not at
TLS or DNS. It prints the response body on a non-200, because these handlers put
the cause in `detail` — a bare status code sends you to the journal for something
the reply already contained.

One parameter-free path per thing a deploy can break:

| path | proves |
|---|---|
| `/` | the code tree and `web_root` |
| `/api/corpus/traditions` | `config/`, which ships with the code |
| `/api/corpus/documents` | `outputs/corpus` is readable *by the service* |
| `/api/motifs/indexes` | `outputs/motifs` |
| `/api/similarity/models` | the ChromaDB store opens — 503 if not |

`outputs/projections` and `outputs/graphs` stay uncovered: their routes need a
model or document id, so probing them means fetching a listing first. The corpus
row is the interesting one — it was added after a 0600 `corpus.json` shipped a
500 to production past a green smoke run, because the only corpus path checked
until then read `config/`, not the store.

---

## 3. Constraints the code imposes

These are not style choices — each one breaks something if ignored.

- **The loopback port is a contract between two files.** The app binds whatever
  `MYTHO_SERVER__PORT` says in `/etc/mythoscope/env`; Caddy proxies whatever
  `APP_PORT` in `fabfile.py` substituted into `${PORT}` in the Caddyfile. Move
  one and the site 502s while the app itself stays healthy on loopback — and the
  smoke check, which reads the port from the env file, would have passed. So
  `_smoke` compares the two first and refuses to continue if they disagree. To
  actually change the port: set `APP_PORT`, re-run `bootstrap`, and edit the env
  file on the server (`bootstrap` will not overwrite it).
- **`WorkingDirectory` is load-bearing.** `settings.py` defaults every path to a
  *relative* one: `config`, `outputs/*`, and `web_root = src/server/web`. Start
  the server anywhere else and you get a 404 index and empty API responses.
  Hence `WorkingDirectory=/srv/mythoscope/app` plus the `app/outputs` symlink.
- **The service writes to disk.** `setup_logging()` runs in the `mytho` group
  callback (`src/cli.py`), so *every* invocation — `server` included — does
  `logs_dir.mkdir(...)` and opens a `FileHandler`. That is why the unit needs
  `ReadWritePaths=/srv/mythoscope` under `ProtectSystem=strict`, and why the
  swap chmods `outputs/logs` group-writable. It already installs a
  `StreamHandler` too, so journald sees everything; going stdout-only later
  means *dropping* the file handler, not adding anything. `_prune_old_logs`
  keeps `logs_max_files` (20), so the directory is bounded.
- **What the service writes, the deploy user has to be able to delete.**
  `push-outputs` removes the old store, and unlinking a file needs write on the
  directory holding it — not on the file. Under systemd's default `UMask=0022` a
  directory the service creates lands `drwxr-sr-x`: group-readable, group
  *un*writable, so `ubuntu` cannot remove anything inside it and the swap dies
  with `rm: cannot remove '…/embeddings/chroma.sqlite3': Permission denied`.
  Chroma creates its own directory when the path is missing, so this is reachable
  simply by starting the service before the first `push-outputs`. The unit
  therefore sets `UMask=0002`, and the swap removes the previous store with
  `sudo` for trees that predate it.
- **`cli.py` is on the server's import path.** `ExecStart` is `mytho server`, so
  every module-scope import in `src/cli.py` runs before uvicorn does. Importing
  anything from `pipeline` there is fatal on a viewer venv: `pipeline/__init__`
  eagerly pulls every stage, so `pipeline.caches` — two stdlib imports of its
  own — drags in pymupdf, trafilatura, openai and torch behind it. Command
  bodies therefore import their dependencies locally. That is a deliberate
  exception to the imports-at-top rule, and the module docstring says so.
- **`--extra viewer` is sufficient, and is what we install.** Verified the way
  the server actually runs: a venv built with `--extra viewer` alone, then
  `mytho server` started against the real `outputs/` and every GET route in
  `openapi.json` exercised with live parameters — 200 across the board, the
  heavy projections route included (2.18MB gzipped, matching §4). Verifying by
  importing `src/server/**` instead is what let the `cli.py` breakage above
  through: it never touches the entry point. `src/corpus/__init__.py` and
  `src/graphs/__init__.py` are empty, `src/projections/__init__.py` is a literal
  list, and `graphs.store` / `motifs.store` / `corpus.traditions_config` import
  only stdlib + `settings`. The `corpus` and `graphs` extras would add requests,
  beautifulsoup4, trafilatura, fake-useragent, PyMuPDF, openai and networkx —
  all build-side. `EXTRAS` in `fabfile.py` is a one-line constant if that
  changes.
- **Text search 503s by design.** It needs sentence-transformers + torch, which
  `viewer` omits, and is gated behind `MYTHO_SERVER__TEXT_SEARCH` (default
  false). Enabling it means adding the `search` extra — and ~2.5GB of torch.

### Python version

Pinned to **3.13** via `.python-version` (rsynced; `uv sync` provisions it on
the server, downloading a managed CPython if the system lacks one).

**The interpreter must not land in a home directory.** uv installs managed
CPythons under `$HOME/.local/share/uv/python`, and a venv's `bin/python` is a
*symlink* into that tree — so under `ProtectHome=true` the service cannot see
its own interpreter and dies `203/EXEC` (and `/home/ubuntu` is `0750`, which
would block the service user anyway). `deploy` therefore sets
`UV_PYTHON_INSTALL_DIR=/opt/mythoscope-python`, which `bootstrap` creates
`ubuntu:mythoscope 2775`: writable by the deploy user, and outside
`ReadWritePaths` so `ProtectSystem=strict` leaves it read-only for the service.
Only images that already ship 3.13 (Debian 13, Ubuntu 25.04+) skip the download
and link `/usr/bin/python3.13` instead; on 24.04 LTS it always happens.

3.12 is not actually old — security support runs to 2028 — but 3.13 is equally
well covered by this stack now. 3.14 was rejected: the pinned uv only offers it
as `3.14.0b1`, and this project depends on torch (`embeddings`) and numba via
umap-learn (`analysis`), historically the two slowest projects to publish wheels
for a new interpreter. Avoid the `+freethreaded` variants for the same reason;
since the projections work is cached, the GIL is no longer the bottleneck anyway.

The existing `uv.lock` already satisfies 3.13 (`uv lock --check` passes, no
re-resolve), and the full suite plus a live smoke test against the real ChromaDB
store pass on 3.13.3.

---

## 4. Performance

Measured on a 20-core dev box against the real `outputs/`, single uvicorn worker.

### Handler model

All 15 route handlers are plain `def` — zero `async def`. That is correct here:
Starlette runs sync handlers in a threadpool (anyio default limiter = 40
tokens), so one slow request cannot block the event loop. Had they been
`async def`, a single 400ms projection would have stalled every other request in
the process.

### Baseline (all endpoints except projections)

| endpoint | p50 | payload | req/s @ conc 1 | req/s @ conc 16 |
|---|---|---|---|---|
| `/api/motifs/berezkin/stats` | 0.6 ms | 11 KB | 1637 | 2966 |
| `/api/corpus/traditions` | 0.8 ms | 18 KB | — | — |
| `/api/graphs/{doc}/beings` | 0.9 ms | 47 KB | — | — |
| `/api/similarity/points/…` | 3.0 ms | 10 KB | 453 | 698 |

Light endpoints scale only ~1.8× from 1→16 concurrency on 20 cores: pure-Python
JSON work under the GIL. At ~3000 req/s it does not matter.

### The projections bottleneck, and the fix

`/api/similarity/projections/{model}/{method}` serves an ~8MB document. The
original code rebuilt it on **every** request, and the cost decomposed as:

| step | cost |
|---|---|
| `json.loads` from disk | 26.6 ms |
| `json.dumps` — FastAPI re-encoding the dict it had just decoded | 27.8 ms |
| `GZipMiddleware` compressing the result (level 9, its default) | 321.2 ms |
| pydantic `ProjectionData` validation (`extra="allow"`, one fixed field) | negligible |

Before/after, same box, same data:

| path | before | after | |
|---|---|---|---|
| **gzip** (what browsers send) @ conc 1 | **2.1 req/s**, p50 472 ms | **~650 req/s**, p50 1.3 ms | ~300× |
| gzip @ conc 16 | 2.2 req/s, p50 **6856 ms** | ~640 req/s, p50 23 ms | ~290× |
| identity (no `Accept-Encoding`) @ conc 1 | 24 req/s, p50 41 ms | ~155 req/s, p50 6.3 ms | ~6× |
| identity @ conc 40 | 28 req/s, p95 1474 ms | ~113 req/s, p95 544 ms | |
| revalidate (`If-None-Match` → 304) | n/a | ~2400–3700 req/s | |

Before the fix, throughput was **flat at ~2 req/s regardless of concurrency**,
with latency growing linearly — the signature of a GIL-bound workload where
extra threads only queue. Note the original benchmark used curl/urllib, which
send no `Accept-Encoding`; that measured the 24 req/s identity path and *missed*
the 321ms gzip cost that every real browser was paying.

The fix (`src/server/services/projections.py`): decode, encode and gzip once,
cache the finished buffers keyed on the file's mtime+size, and hand them out.
The route returns a `Response` directly, which bypasses `response_model`
serialization on purpose. `GZipMiddleware` passes a body through untouched once
`Content-Encoding` is set (`content_encoding_set` in Starlette's responder), so
the cached gzip is not compressed twice. An ETag lets a revalidating client skip
the transfer entirely.

Payload also shrank: compact JSON separators took the identity body from
~7.83MB to 7.54MB, and the wire form is 2.18MB gzipped.

Cache invalidation is the file's identity, so a `push-outputs` swap is picked up
without special handling — and the swap restarts the service anyway.

### Memory

| state | before | after |
|---|---|---|
| fresh start | 90 MB | 90 MB |
| after light requests (motifs/corpus cached per process) | 223 MB | 223 MB |
| after first chroma query (HNSW index resident) | 348 MB | 351 MB |
| steady state | 368 MB | 375 MB (all 5 projections cached) |
| **peak under 40-concurrent projections load** | **784 MB** | **378 MB** |

The old peak was the same bug: 40 in-flight requests each holding their own
decoded 8MB document. The cache costs a fixed ~48MB and removes the churn
entirely. RSS is stable — no leak in either version.

### When to add workers

Not yet. At ~650 req/s on the heaviest endpoint and ~3000 req/s on the rest, one
worker is far from the ceiling for a read-only viewer.

The trigger is sustained load pinning one core at 100% with p95 climbing.
`run_server.py` passes no `workers=` today, so that is a small code change — and
because the production workload is read-only, it does **not** have to wait for
ChromaDB to be extracted (§5 verifies concurrent readers). Budget ~180MB per
extra worker: each one holds its own resident HNSW index and its own projections
cache.

---

## 5. ChromaDB

### Telemetry is off

Chroma's `anonymized_telemetry` defaults to **true**, with
`chromadb.telemetry.product.posthog.Posthog` behind it — a public box would
otherwise post usage events outbound on its own initiative. `_get_client()` in
`src/embeddings/chroma_manager.py` passes `Settings(anonymized_telemetry=False)`,
which covers every machine that opens the store, not just the server. Doing it
there rather than via the `ANONYMIZED_TELEMETRY` environment variable keeps it
from depending on an operator not deleting a line from the env file.

### In production the server only reads

Every Chroma call in `src/server/` is a read — `list_collections`,
`get_collection`, `count`, `get`, `query`. The mutating wrappers on
`ChromaCollection` (`upsert`, `delete`, `modify`) and `get_or_create_collection`
are called only from `src/embeddings/build_embeddings.py`, i.e. the pipeline,
which does not run on the server. The store arrives prebuilt in `outputs/` and
is replaced wholesale by `push-outputs`.

### But the store still has to be writable

Read-only *at the application level* is not read-only *on disk*. Opening a
`PersistentClient` writes to `chroma.sqlite3` before any query runs: it inserts
a row into an internal `acquire_write` table — a writability probe that is never
cleaned up (today's store carries ~50 rows, one per client open since the store
was built). Measured on a copy of the real store: pristine → open a client →
`md5` differs, with `acquire_write` the only table whose contents changed.
Against a store with the write bit cleared, the client does not open at all:

```
InternalError: error returned from database: (code: 8) attempt to write a readonly database
```

Three consequences, all already handled but worth knowing:

- **group ownership *and* the group write bit, or the store will not open.**
  This is the one place where the rsync ownership problem in §1 is fatal rather
  than cosmetic. A locally-built `chroma.sqlite3` is `0644` in the builder's own
  group, and rsync carries both over; the service can then read every byte of
  the store and still not open it. The symptom is one failing route —
  `/api/similarity/models` → `Embedding store unavailable: … attempt to write a
  readonly database` — while everything else is green, because nothing else
  touches Chroma. `push-outputs` regroups the staged tree and additionally
  chmods `embeddings/` to `0664` before the swap. It must also stay covered by
  `ReadWritePaths` (§3) — a hardening tweak making `outputs/` read-only would
  take the site down at the first request, not at deploy time;
- `chroma.sqlite3` on the server drifts from the local copy byte-wise even
  though no data changed, so rsync always sees it as modified. It is
  delta-transferred, so the cost is reading 175MB on each side, not sending it;
- the journal mode is `delete`, not WAL — a writer takes an exclusive lock over
  the whole database. Never point the pipeline at a live store; readers would
  get `SQLITE_BUSY`. This is why `push-outputs` stops the service.

### Which does make workers safe

With a read-only workload the multi-process objection disappears: nothing
invalidates a peer's HNSW cache because nothing writes. Verified directly —
three processes opened the same store concurrently and ran 200 queries each,
no lock contention, each opening in 0.06s.

The cost is memory, and it is per-process, not shared:

| per reader process | RSS |
|---|---|
| after `import chromadb` | ~77MB |
| after opening the collection | ~205MB |
| after 200 queries | ~205MB (index is resident at open, not lazily) |

So ~128MB of store residency per worker, plus that worker's own projections
cache (§4) — call it ~180MB per extra worker. That is the real budget question,
and it is why §4 recommends raising thread capacity before adding processes.

**Extract it into its own service when** — and only when — one of these is true:

- query load needs more workers than memory comfortably allows, and sharing one
  resident index across them is cheaper than replicating it;
- writes need to happen while the server serves — this would remove the
  stop/swap/start dance in `push-outputs` entirely, and is the one case where
  the single-writer rule genuinely bites;
- something other than the viewer needs the same store.

**The migration is small, because the seam already exists.** `_get_client()` is
the single place a client is constructed — a module-level singleton. The change
is:

1. `chroma run --path /srv/mythoscope/outputs/embeddings` as its own systemd
   unit on loopback;
2. `_get_client()` returns `chromadb.HttpClient(...)` behind a settings flag.

One function, one unit file. Workers then become unambiguously safe.

---

## 6. Why not Docker

Considered and rejected for now:

- `uv sync --frozen` already delivers the reproducibility that is Docker's main
  draw here, using the same command developers run locally.
- The 368MB store would be a bind mount either way, so the data is not
  containerized regardless — you would take the volume management without the
  isolation benefit.
- Embedded Chroma writing to a bind-mounted SQLite file adds a uid-mismatch
  failure mode for zero gain.
- Native Caddy does ACME and cert renewal with no configuration; in a container
  that becomes cert-volume persistence to manage.
- Deploy cost: rsync + `uv sync` + restart is ~10s, against build/push/pull and
  a registry.

Revisit when a second service with conflicting dependencies appears. The systemd
work is not wasted then — the unit becomes a compose service and the rsync
stays. The file-logging change noted in §3 is the natural precursor.

---

## 7. Open items

- Latent packaging bug, not blocking: `cli.py` and `export_bundle.py` import
  `pipeline.caches`, but `pipeline` is in neither `py-modules` nor
  `packages.find.include` in `pyproject.toml`. It resolves only because
  `uv sync` installs the project editable. A real wheel build would ship a
  broken `mytho`.
- `tests/test_model_manager.py` and `tests/test_reduce_dimensions.py` import
  torch and umap at module level, so the suite cannot run green without the
  `embeddings` / `analysis` extras installed. Unrelated to deployment, but it
  makes "run the tests before deploying" awkward on a lean venv.
