# Codex with SambaNova MiniMax 2.5

A LiteLLM proxy configuration for running SambaNova models (MiniMax-M2.5) with Docker, with full prompt/completion logging and Codex CLI integration.

## What You'll Achieve

- **Run Codex with SambaNova's MiniMax-M2.5 model** — Fast inference and low token pricing
- **Integrate with LiteLLM** — Automatically log all prompts, completions, and costs to PostgreSQL

## Prerequisites

- Docker & Docker Compose
- SambaNova API key (get one at [sambanova.ai](https://sambanova.ai))
- A machine running macOS or Linux

## Quick Start

### Step 1: Install Codex CLI

```bash
npm i -g @openai/codex@0.57.0
```

> We recommend version 0.57.0 for stable compatibility with LiteLLM.

### Step 2: Clone the Project

```bash
git clone https://github.com/reginold/litellm-sambanova.git
cd litellm-sambanova
```

### Step 3: Set Environment Variables

```bash
export SAMBANOVA_API_KEY="your-sambanova-api-key"
export LITELLM_MASTER_KEY="your-master-key"
export CODEX_LITELLM_KEY="your-master-key"
```

### Step 4: Configure Token Pricing and Database

Edit `proxy_config.yaml`:

```yaml
model_list:
  - model_name: MiniMax-M2.5
    litellm_params:
      model: openai/MiniMax-M2.5
      api_key: os.environ/SAMBANOVA_API_KEY
      api_base: https://api.sambanova.ai/v1
    model_info:
      input_cost_per_token: 0.0000003
      output_cost_per_token: 0.0000012
      tpm: 1000000
      rpm: 100

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  store_model_in_db: true
  store_prompts_in_spend_logs: true
```

#### Why `openai/MiniMax-M2.5` instead of `sambanova/MiniMax-M2.5`?

- **Tool/Function Calling Support** — SambaNova's native API (`sambanova/`) does not support Codex's tool use features. You'll get: `litellm.UnsupportedParamsError: sambanova does not support parameters: ['tools']`
- **OpenAI-Compatible Format** — By using the `openai/` prefix, LiteLLM routes through its OpenAI-compatible interface for better compatibility
- **Same Backend** — The actual API call still goes to SambaNova's endpoint, so you still get fast inference and low pricing

### Step 5: Start LiteLLM and PostgreSQL

```bash
docker compose up --build
```

This starts two services:

- **LiteLLM Proxy** on port 4000
- **PostgreSQL** on port 5433 (internal port 5432)

> If you modify `proxy_config.yaml`, run `docker compose restart litellm` to apply changes.

### Step 6: Configure Codex CLI

Create or update `~/.codex/config.toml`:

```toml
[model_providers.openai]
name = "LiteLLM Local"
base_url = "http://localhost:4000/v1"
env_key = "CODEX_LITELLM_KEY"
wire_api = "chat"
query_params = { "temperature" = "1", "do_sample" = "true" }

[sandbox_workspace_write]
network_access = true
```

> Use `wire_api = "chat"` because LiteLLM exposes `/v1/chat/completions` as its main endpoint.

### Step 7: View Logs and Data

#### Option A: LiteLLM UI

Access http://localhost:4000 and log in with your `LITELLM_MASTER_KEY` to:
- View request logs — See all prompts and completions
- Monitor spending — Track costs by model and time period
- Check model status — Verify MiniMax-M2.5 is online

#### Option B: Direct PostgreSQL Access

```bash
docker compose exec postgres psql -U litellm -d litellm
```

> Use double quotes around table names: `"LiteLLM_SpendLogs"`

Useful SQL queries:

```sql
-- View recent requests
SELECT * FROM "LiteLLM_SpendLogs" ORDER BY "startTime" DESC LIMIT 10;

-- Check spend by model
SELECT model, SUM(spend) as total_spend FROM "LiteLLM_SpendLogs" GROUP BY model;

-- View token usage by model
SELECT model, SUM(prompt_tokens) as total_prompt_tokens,
       SUM(completion_tokens) as total_completion_tokens
FROM "LiteLLM_SpendLogs" GROUP BY model;
```

## Token Pricing

MiniMax-M2.5 rates:
- **Input:** $0.30 per 1M tokens
- **Output:** $1.20 per 1M tokens

## Troubleshooting

See [log.md](log.md) for detailed issue resolutions.

| Issue | Solution |
|-------|----------|
| Port already in use | Change port in docker-compose.yml |
| Postgres not ready | Run `docker compose restart litellm` |
| Model not found | Check proxy_config.yaml syntax |

## Git Push

```bash
git add .
git commit -m "Your commit message"
git push origin main
```
