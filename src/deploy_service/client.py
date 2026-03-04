"""TrueFoundry API client for workspace lookup and deployment."""
from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

_default_client: httpx.Client | None = None


def _client() -> httpx.Client:
    global _default_client
    if _default_client is None:
        _default_client = httpx.Client(timeout=60.0)
    return _default_client


def _credentials() -> tuple[str, str]:
    base_url = (os.getenv("TFY_BASE_URL") or "").strip()
    api_key = (os.getenv("TFY_API_KEY") or "").strip()
    if not base_url or not api_key:
        raise ValueError(
            "Set TFY_BASE_URL and TFY_API_KEY (env or .env). "
            "See https://docs.truefoundry.com/docs/generating-truefoundry-api-keys"
        )
    return base_url.rstrip("/"), api_key


def get_workspace_id(workspace_fqn: str) -> str:
    """Resolve workspace FQN (cluster-id:workspace-name) to internal workspace ID."""
    if ":" not in workspace_fqn:
        raise ValueError(
            f"Workspace FQN must be 'cluster-id:workspace-name', not just a cluster ID. "
            f"Got: {workspace_fqn!r}. "
            "List workspaces: GET /api/svc/v1/workspaces (or use clusterId to filter), then use the 'fqn' from a workspace."
        )
    base_url, api_key = _credentials()
    resp = _client().get(
        f"{base_url}/api/svc/v1/workspaces",
        params={"fqn": workspace_fqn},
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    items = (
        data
        if isinstance(data, list)
        else data.get("data", data.get("items", data.get("results", [])))
    )
    if not items:
        raise ValueError(
            f"No workspace found for FQN: {workspace_fqn!r}. "
            "FQN must be 'cluster-id:workspace-name' (e.g. tfy-usea1-devtest:my-workspace). "
            "List workspaces: curl -s -H \"Authorization: Bearer $TFY_API_KEY\" \"$TFY_BASE_URL/api/svc/v1/workspaces\" (or add ?clusterId=CLUSTER_ID)"
        )
    first = items[0] if isinstance(items[0], dict) else items
    wid = first.get("id") if isinstance(first, dict) else getattr(first, "id", None)
    if not wid:
        raise ValueError(f"Workspace response missing id for FQN: {workspace_fqn}")
    return str(wid)


def create_deployment(manifest: dict[str, Any], workspace_id: str, options: dict[str, Any] | None = None) -> Any:
    """Create or update an application deployment. PUT /api/svc/v1/apps."""
    base_url, api_key = _credentials()
    body: dict[str, Any] = {"manifest": manifest, "workspaceId": workspace_id}
    if options:
        body.update(options)
    resp = _client().put(
        f"{base_url}/api/svc/v1/apps",
        json=body,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json", "Content-Type": "application/json"},
    )
    if not resp.is_success:
        try:
            err_body = resp.json()
        except Exception:
            err_body = resp.text[:1000] if resp.text else ""
        msg = f"Client error '{resp.status_code} {resp.reason_phrase}' for url '{resp.url}'"
        if err_body:
            msg += f". Response: {err_body}"
        raise ValueError(msg)
    ct = resp.headers.get("Content-Type", "")
    if "application/json" in ct:
        return resp.json()
    return resp.text
