# deploy-service

Deploy **one** TrueFoundry service that runs **multiple stdio MCP servers** in a single process, using [TBXark mcp-proxy](https://github.com/TBXark/mcp-proxy). One HTTP endpoint aggregates multiple stdio backends (e.g. E2B MCP with different API keys per user).

## What’s in this repo

- **`multi-stdio/`** — Dockerfile, config template, and entrypoint for TBXark mcp-proxy (multiple stdio backends, one server).
- **`manifest.multi-stdio.yaml`** — TrueFoundry manifest (Git-based build, no docker push).
- **`src/deploy_service/`** — Small Python CLI to deploy a manifest to TrueFoundry.

## Setup

1. **Credentials** (env or `.env` in repo root):
   - `TFY_BASE_URL` — TrueFoundry control plane URL  
   - `TFY_API_KEY` — API key ([docs](https://docs.truefoundry.com/docs/generating-truefoundry-api-keys))

2. **Install** (optional, for CLI):
   ```bash
   cd deploy-service && pip install -e .
   ```
   Or run without installing: `PYTHONPATH=src python -m deploy_service.cli ...`

## 1. Configure the manifest

Edit **`manifest.multi-stdio.yaml`**:

- **`image.build_source.repo_url`** and **`branch_name`** — Your Git repo (e.g. this repo).
- **`image.build_spec.dockerfile_path`** and **`build_context_path`** — Match your repo layout. If the repo root is the parent of `deploy-service`, use:
  - `dockerfile_path: deploy-service/multi-stdio/Dockerfile`
  - `build_context_path: deploy-service`
- **`workspace_fqn`** — Your workspace (e.g. `tfy-usea1-devtest:tryout`).
- **`ports[0].host`** — Hostname for the service (e.g. `tryout.tfy-usea1-ctl.devtest.truefoundry.tech`).
- **`env`** — Set `E2B_API_KEY_USER1`, `E2B_API_KEY_USER2` (or use TrueFoundry secrets). The entrypoint injects these into the proxy config.

## 2. Deploy

```bash
cd deploy-service

export TFY_WORKSPACE_FQN="tfy-usea1-devtest:tryout"
export TFY_DEPLOY_MANIFEST_FILE="manifest.multi-stdio.yaml"

python -m deploy_service.cli --manifest-file manifest.multi-stdio.yaml --workspace-fqn "$TFY_WORKSPACE_FQN"
```

Or with env overrides from the CLI:

```bash
python -m deploy_service.cli --manifest-file manifest.multi-stdio.yaml --workspace-fqn "cluster:workspace" \
  --env "E2B_API_KEY_USER1=key1" --env "E2B_API_KEY_USER2=key2"
```

TrueFoundry will clone the repo, build the image from `multi-stdio/Dockerfile`, and deploy. No docker push needed.

## 3. Add more stdio backends

To add more users/backends:

1. **`multi-stdio/config.json.template`** — Add a new entry under `mcpServers`, e.g. `"user3": { "command": "npx", "args": ["-y", "@e2b/mcp-server"], "env": { "E2B_API_KEY": "__E2B_API_KEY_USER3__" } }`.
2. **`multi-stdio/entrypoint.sh`** — Add a `sed` line to substitute `__E2B_API_KEY_USER3__` from `$E2B_API_KEY_USER3`.
3. **`manifest.multi-stdio.yaml`** — Add `E2B_API_KEY_USER3` to `env` (or use secrets).

## CLI reference

| Option | Description |
|--------|-------------|
| `--workspace-fqn` | Workspace FQN (required, or `TFY_WORKSPACE_FQN`) |
| `--manifest-file` | Path to manifest YAML/JSON (required, or `TFY_DEPLOY_MANIFEST_FILE`) |
| `--name` | Override service name from manifest |
| `--env KEY=VALUE` | Env var (repeatable), merged into manifest env |
| `--json` | Print raw JSON response |

## Programmatic use

```python
from deploy_service import deploy

deploy(
    workspace_fqn="tfy-usea1-devtest:tryout",
    manifest_file="manifest.multi-stdio.yaml",
    env_overrides={"E2B_API_KEY_USER1": "key1", "E2B_API_KEY_USER2": "key2"},
)
```
