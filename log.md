# LiteLLM Proxy Setup — Issues & Resolutions

## Issue 1: Port 5432 already in use

**Error:** `listen tcp 0.0.0.0:5432: bind: address already in use`

**Cause:** A local Postgres instance was already running on port 5432.

**Fix:** Changed the host port mapping in `docker-compose.yml` from `"5432:5432"` to `"5433:5432"`. The internal container-to-container connection (DATABASE_URL) still uses 5432, so no other changes were needed.

## Issue 2: `litellm proxy` — unexpected extra argument

**Error:** `Got unexpected extra argument (proxy)`

**Cause:** The `litellm` CLI does not accept `proxy` as a subcommand.

**Fix:** Removed `proxy` from the CMD in the Dockerfile. Correct command is `litellm --host 0.0.0.0 --port 4000 --config /app/proxy_config.yaml`.

## Issue 3: Missing `prisma` module

**Error:** `ModuleNotFoundError: No module named 'prisma'`

**Cause:** The base `python:3.11-slim` image with `litellm[proxy]` did not include the `prisma` package, which is required when `DATABASE_URL` is set.

**Fix (partial):** Added `prisma` to the pip install. This led to Issue 4.

## Issue 4: Missing `libatomic.so.1`

**Error:** `node: error while loading shared libraries: libatomic.so.1: cannot open shared object file`

**Cause:** The `python:3.11-slim` image lacks `libatomic1`, which is needed by the Prisma CLI's bundled Node.js.

**Fix (partial):** Added `apt-get install libatomic1` to the Dockerfile. This led to Issue 5.

## Issue 5: Prisma schema not found / binaries not generated

**Error:** `Could not find Prisma Schema` and later `Unable to find Prisma binaries. Please run 'prisma generate' first.`

**Cause:** Running `prisma generate` at build time fails because LiteLLM's Prisma schema is embedded in the package and expects a specific setup. Building from `python:3.11-slim` doesn't include the pre-generated Prisma client that LiteLLM needs.

**Fix (final):** Replaced the custom Dockerfile entirely with the official LiteLLM Docker image `ghcr.io/berriai/litellm:main-latest`, which has Prisma pre-built. Updated `docker-compose.yml` to use `image:` instead of `build:` and passed CLI args via `command:`.

## Issue 6: Postgres view errors on first startup

**Errors:** `relation "MonthlyGlobalSpend" does not exist`, `relation "LiteLLM_VerificationTokenView" does not exist`, etc.

**Cause:** Normal behavior on first startup. LiteLLM creates these views lazily as they are needed.

**Fix:** No action required — these errors are harmless.

## Issue 7: Codex sends unsupported `tools` parameter

**Error:** `litellm.UnsupportedParamsError: sambanova does not support parameters: ['tools'], for model=MiniMax-M2.5`

**Cause:** Codex sends a `tools` parameter in its API requests, but SambaNova's API does not support it. LiteLLM by default rejects unsupported parameters.

**Fix:** Added `litellm_settings: drop_params: true` to `proxy_config.yaml`. This tells LiteLLM to silently drop any parameters that the downstream provider doesn't support, rather than returning a 400 error. Restart LiteLLM after the change with `docker compose restart litellm`.

## Issue 8: Docker Compose `version` attribute is obsolete

**Warning:** `the attribute 'version' is obsolete, it will be ignored, please remove it to avoid potential confusion`

**Cause:** Modern Docker Compose (v2+) no longer uses the `version` field in `docker-compose.yml`. It's ignored and produces a warning.

**Fix:** Remove the `version: "3.9"` line from `docker-compose.yml`.

## Issue 9: Model shows as `openai` instead of `sambanova` in UI

**Cause:** The model was configured as `openai/MiniMax-M2.5` in `proxy_config.yaml`, so the UI displayed the provider as `openai` even though requests go to SambaNova via `api_base`.

**Fix:** Changed `model` from `openai/MiniMax-M2.5` to `sambanova/MiniMax-M2.5` in `proxy_config.yaml`. Apply with `docker compose restart litellm` or `docker compose up --build`.

## Issue 10: `Application startup failed` — Postgres not ready

**Error:** `httpx.ConnectError: All connection attempts failed` → `Application startup failed. Exiting.`

**Cause:** The `litellm` container starts before Postgres is fully ready to accept connections. `depends_on` alone only waits for the container to start, not for the database to be ready.

**Fix:** Added a health check to the `postgres` service and changed `depends_on` to use `condition: service_healthy`, so LiteLLM waits until Postgres is actually accepting connections.

## Issue 11: Incorrect token pricing

**Cause:** Token costs were set to `0.0000005` / `0.0000015` but SambaNova's actual pricing for MiniMax-M2.5 is $0.30 per 1M input tokens and $1.20 per 1M output tokens.

**Fix:** Updated `proxy_config.yaml` to `input_cost_per_token: 0.0000003` ($0.30/1M) and `output_cost_per_token: 0.0000012` ($1.20/1M).

## Summary

The key takeaway is to **use the official LiteLLM Docker image** (`ghcr.io/berriai/litellm:main-latest`) instead of building from `python:3.11-slim`. It avoids all Prisma-related issues (missing module, missing libatomic, missing schema/binaries).
