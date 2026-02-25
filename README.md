# LiteLLM SambaNova Proxy

A LiteLLM proxy configuration for running SambaNova models (MiniMax-M2.5) with Docker.

## Prerequisites

- Docker & Docker Compose
- SambaNova API key

## Quick Start

### 1. Set Environment Variables

```bash
export SAMBANOVA_API_KEY="your-sambanova-api-key"
export LITELLM_MASTER_KEY="your-master-key"
```

### 2. Start LiteLLM Proxy

```bash
cd /Users/bowenl/work/litellm-sambanova
docker compose up -d
```

### 3. Access the Proxy

- **UI:** http://localhost:4000
- **API:** http://localhost:4000/v1/chat/completions

## Configuration

### Model Config Location

The model configuration is in `proxy_config.yaml`:

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
```

### How to Add a New Model

To add a new model, edit `proxy_config.yaml` and add a new entry to `model_list`:

```yaml
model_list:
  - model_name: Your-Model-Name
    litellm_params:
      model: openai/your-model  # or sambanova/your-model
      api_key: os.environ/YOUR_API_KEY
      api_base: https://api.sambanova.ai/v1  # or your custom endpoint
    model_info:
      input_cost_per_token: 0.000000X
      output_cost_per_token: 0.000000X
      tpm: 1000000
      rpm: 100
```

Then restart LiteLLM:
```bash
docker compose restart litellm
```

### Other Useful Settings

**Drop unsupported params** (for providers that dont support all parameters):
```yaml
litellm_settings:
  drop_params: true
```

**Custom callback settings:**
```yaml
litellm_settings:
  callbacks: ["prometheus"]
```

## Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| litellm | 4000 | LiteLLM proxy UI & API |
| postgres | 5433 | Database (internal port 5432) |

## Troubleshooting

See `log.md` for detailed issue resolutions.

### Common Issues

- **Port already in use:** Change port in `docker-compose.yml`
- **Postgres not ready:** Use `docker compose restart litellm`
- **Model not found:** Check `proxy_config.yaml` syntax

## Git Push

To push changes to GitHub:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

If you get authentication errors, see `log.md` for resolution (use PAT or SSH).
