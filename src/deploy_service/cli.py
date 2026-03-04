"""CLI: deploy the multi-stdio (or any) service to TrueFoundry."""
from __future__ import annotations

import argparse
import json
import os
import sys

from .deploy import deploy


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy one TrueFoundry service (e.g. multi-stdio MCP server) from a manifest."
    )
    parser.add_argument(
        "--workspace-fqn",
        default=os.environ.get("TFY_WORKSPACE_FQN"),
        help="Workspace FQN (cluster-id:workspace-name). Default: TFY_WORKSPACE_FQN.",
    )
    parser.add_argument(
        "--manifest-file",
        default=os.environ.get("TFY_DEPLOY_MANIFEST_FILE"),
        help="Path to manifest YAML/JSON. Default: TFY_DEPLOY_MANIFEST_FILE.",
    )
    parser.add_argument(
        "--name",
        metavar="NAME",
        help="Override service name from manifest.",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Env var (repeatable). Merged into manifest env.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON response.",
    )
    args = parser.parse_args()

    if not args.workspace_fqn:
        print("Error: --workspace-fqn or TFY_WORKSPACE_FQN is required.", file=sys.stderr)
        sys.exit(1)
    if not args.manifest_file:
        print("Error: --manifest-file or TFY_DEPLOY_MANIFEST_FILE is required.", file=sys.stderr)
        sys.exit(1)

    env = {}
    for s in args.env:
        if "=" in s:
            k, _, v = s.partition("=")
            env[k.strip()] = v.strip()

    try:
        result = deploy(
            workspace_fqn=args.workspace_fqn,
            manifest_file=args.manifest_file,
            name_override=args.name,
            env_overrides=env or None,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("Deployed:", result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
