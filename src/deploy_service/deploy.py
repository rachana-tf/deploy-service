"""Deploy one service (multi-stdio or any manifest) to TrueFoundry."""
from __future__ import annotations

import copy
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from .client import create_deployment, get_workspace_id


def _load_manifest(path: str | Path | None) -> dict[str, Any]:
    if not path:
        raise ValueError("Provide a manifest file (--manifest-file or env TFY_DEPLOY_MANIFEST_FILE)")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest file not found: {p}")
    raw = p.read_text()
    if p.suffix in (".yaml", ".yml"):
        return yaml.safe_load(raw) or {}
    if p.suffix == ".json":
        import json
        return json.loads(raw)
    return yaml.safe_load(raw) or {}


def _is_git_build(manifest: dict[str, Any]) -> bool:
    image = manifest.get("image") or {}
    return image.get("type") == "build" and (image.get("build_source") or {}).get("type") == "git"


def deploy(
    workspace_fqn: str,
    manifest_file: str | Path | None = None,
    name_override: str | None = None,
    env_overrides: dict[str, str] | None = None,
    use_tfy_deploy_for_build: bool = True,
) -> Any:
    """Deploy a single service from a manifest.

    If the manifest uses a Git build source (type: build, build_source.type: git),
    runs `tfy deploy -f <manifest>` (requires tfy CLI). Otherwise uses PUT /api/svc/v1/apps.

    Args:
        workspace_fqn: Workspace FQN (cluster-id:workspace-name).
        manifest_file: Path to manifest YAML/JSON (or TFY_DEPLOY_MANIFEST_FILE).
        name_override: If set, override manifest name.
        env_overrides: Optional env vars to merge into manifest.env.
        use_tfy_deploy_for_build: If True, use tfy deploy for Git-build manifests when tfy is available.

    Returns:
        API response or dict with deploy output when using tfy deploy.
    """
    path = manifest_file or os.environ.get("TFY_DEPLOY_MANIFEST_FILE")
    path = Path(path).resolve()
    manifest = copy.deepcopy(_load_manifest(path))
    if name_override:
        manifest["name"] = name_override
    if env_overrides:
        base_env = manifest.get("env") or {}
        if isinstance(base_env, dict):
            manifest["env"] = {**base_env, **env_overrides}
        else:
            manifest["env"] = dict(env_overrides)

    if use_tfy_deploy_for_build and _is_git_build(manifest):
        tfy = os.environ.get("TFY_CLI_PATH", "tfy")
        env = os.environ.copy()
        base_url = (os.environ.get("TFY_BASE_URL") or "").strip()
        if base_url and "TFY_HOST" not in env:
            env["TFY_HOST"] = base_url
        try:
            out = subprocess.run(
                [tfy, "deploy", "-f", str(path), "--no-wait"],
                capture_output=True,
                text=True,
                env=env,
                timeout=120,
            )
            if out.returncode != 0:
                raise ValueError(out.stderr or out.stdout or f"tfy deploy exited {out.returncode}")
            return {"ok": True, "message": "tfy deploy started", "output": out.stdout or ""}
        except FileNotFoundError:
            raise ValueError(
                "Manifest uses Git build source; tfy CLI is required. Install it or set TFY_CLI_PATH."
            ) from None

    workspace_id = get_workspace_id(workspace_fqn)
    return create_deployment(manifest, workspace_id)
