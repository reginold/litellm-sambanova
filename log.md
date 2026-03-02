# Setup — Issues & Resolutions

## Issue 1: Port 5432 already in use

**Error:** `listen tcp 0.0.0.0:5432: bind: address already in use`

**Cause:** A local Postgres instance was already running on port 5432.

**Fix:** Changed the host port mapping in `docker-compose.yml` from `"5432:5432"` to `"5433:5432"`.

## Issue 2: `litellm proxy` — unexpected extra argument

**Error:** `Got unexpected extra argument (proxy)`

**Cause:** The `litellm` CLI does not accept `proxy` as a subcommand.

**Fix:** Use `litellm --host 0.0.0.0 --port 4000 --config /app/proxy_config.yaml`.

## Issue 3: Missing `prisma` module

**Error:** `ModuleNotFoundError: No module named 'prisma'`

**Cause:** Base image lacks Prisma when DATABASE_URL is set.

**Fix:** Use the official LiteLLM Docker image (`ghcr.io/berriai/litellm:main-latest`) which has Prisma pre-built.

## Issue 4: Missing `libatomic.so.1`

**Error:** `node: error while loading shared libraries: libatomic.so.1`

**Fix:** Use official LiteLLM image (Issue 3 fix).

## Issue 5: Prisma schema not found / binaries not generated

**Error:** `Could not find Prisma Schema`

**Fix:** Use official LiteLLM Docker image with pre-generated Prisma client.

## Issue 6: Postgres view errors on first startup

**Errors:** `relation "MonthlyGlobalSpend" does not exist`

**Cause:** Normal behavior - views are created lazily.

**Fix:** No action needed.

## Issue 7: Codex sends unsupported `tools` parameter

**Error:** `litellm.UnsupportedParamsError: sambanova does not support parameters: ['tools']`

**Fix:** Add to `proxy_config.yaml`:
```yaml
litellm_settings:
  drop_params: true
```

## Issue 8: Docker Compose version attribute obsolete

**Fix:** Remove `version: "3.9"` from `docker-compose.yml`.

## Issue 9: Model shows as `openai` instead of `sambanova` in UI

**Fix:** Change model from `openai/MiniMax-M2.5` to `sambanova/MiniMax-M2.5` in `proxy_config.yaml`.

## Issue 10: Application startup failed — Postgres not ready

**Error:** `httpx.ConnectError: All connection attempts failed`

**Fix:** Added health check to postgres and `depends_on: condition: service_healthy`.