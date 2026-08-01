from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


EXAMPLE_ROOT = Path(__file__).parent
PROFILE_PATH = EXAMPLE_ROOT.parent / "trino_safe_profile.json"


def installed_command(name: str) -> str:
    command = shutil.which(name)
    if command is None:
        raise RuntimeError(f"installed command is unavailable: {name}")
    return command


def successful_payload(result: Any, operation: str) -> dict[str, Any]:
    if result.isError or not isinstance(result.structuredContent, dict):
        raise RuntimeError(f"MCP operation failed: {operation}")
    return result.structuredContent


async def run_example(workspace: Path) -> dict[str, Any]:
    if workspace.exists():
        raise FileExistsError(f"workspace already exists: {workspace}")
    trino_command = installed_command("test-data-agent-mcp-trino")
    generator_command = installed_command("test-data-agent-mcp-generator")
    workspace.mkdir(parents=True)

    trino_environment = {
        **os.environ,
        "TRINO_ALLOWED_CATALOGS": "memory",
        "TRINO_ALLOWED_SCHEMAS": "default",
        "TRINO_HTTP_SCHEME": "http",
        "TRINO_ALLOW_INSECURE_HTTP": "true",
    }
    trino_server = StdioServerParameters(
        command=trino_command,
        env=trino_environment,
    )
    async with stdio_client(trino_server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            trino_tools = sorted(tool.name for tool in (await session.list_tools()).tools)
            rejected = await session.call_tool(
                "describe_table",
                arguments={
                    "catalog": "production",
                    "schema": "default",
                    "table": "orders",
                },
            )
            rejection_text = " ".join(
                item.text for item in rejected.content if hasattr(item, "text")
            )
            if not rejected.isError or "catalog is not allowed" not in rejection_text:
                raise RuntimeError("Trino MCP did not reject the disallowed catalog")

    generator_server = StdioServerParameters(
        command=generator_command,
        env={**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(workspace)},
    )
    async with stdio_client(generator_server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            generator_tools = sorted(
                tool.name for tool in (await session.list_tools()).tools
            )
            profile = json.loads(PROFILE_PATH.read_text())
            plan = successful_payload(
                await session.call_tool(
                    "plan_trino_dataset",
                    arguments={
                        "profile_payload": profile,
                        "workspace_path": "agent/orders",
                        "count": 8,
                        "seed": 161803,
                        "output_format": "json",
                    },
                ),
                "plan_trino_dataset",
            )
            inspection = successful_payload(
                await session.call_tool(
                    "inspect_dataset_plan",
                    arguments={"workspace_path": "agent/orders"},
                ),
                "inspect_dataset_plan",
            )
            reviewed_sha256 = inspection["review"]["current_spec_sha256"]
            approval = successful_payload(
                await session.call_tool(
                    "approve_dataset_plan",
                    arguments={
                        "workspace_path": "agent/orders",
                        "reviewed_spec_sha256": reviewed_sha256,
                    },
                ),
                "approve_dataset_plan",
            )

    result = {
        "trino_tools": trino_tools,
        "raw_sql_exposed": "run_safe_select" in trino_tools,
        "unsafe_request_rejected": True,
        "generator_tools": generator_tools,
        "approval_required_before_review": plan["approval_required"],
        "reviewed_spec_sha256": reviewed_sha256,
        "row_counts": approval["row_counts"],
        "validation_valid": approval["validation_valid"],
        "synthetic": approval["synthetic"],
        "source_rows_copied": approval["source_rows_copied"],
    }
    (workspace / "example_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    result = asyncio.run(run_example(args.workspace))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
