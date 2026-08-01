"""Build deterministic, row-free public contract fixtures."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest.mock import patch

import test_data_agent
from test_data_agent.agent import build_agent_advisor_exchange
from test_data_agent.cli import build_parser
from test_data_agent.io import load_dataset_spec
from test_data_agent.mcp_generator_server import (
    generate_dataset,
    mcp as generator_mcp,
    plan_trino_dataset,
)
from test_data_agent.mcp_trino_server import trino_mcp_tools
from test_data_agent.mcp_trino_transport import create_trino_mcp


CONTRACT_FIXTURE_NAMES = (
    "advisor-exchange.json",
    "artifact-layout.json",
    "cli-agent-plan.json",
    "cli-parser-surface.json",
    "contract-catalog.json",
    "dataset-spec.json",
    "generation-manifest.json",
    "mcp-generate.json",
    "mcp-generator-tools.json",
    "mcp-plan.json",
    "mcp-trino-tools.json",
    "public-python-api.json",
    "validation-report.json",
)
FIXED_PLAN_ID = "0" * 32


def build_contract_fixtures(workspace_root: Path) -> dict[str, Any]:
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspace_root = workspace_root.resolve()
    previous_workspace = os.environ.get("TEST_DATA_AGENT_WORKSPACE_ROOT")
    os.environ["TEST_DATA_AGENT_WORKSPACE_ROOT"] = str(workspace_root)
    try:
        with patch(
            "test_data_agent.agent_planning.secrets.token_hex",
            return_value=FIXED_PLAN_ID,
        ):
            mcp_plan = plan_trino_dataset(
                _safe_trino_profile(),
                "agent/orders",
                count=3,
                seed=73,
                output_format="json",
            )
            agent_workspace = workspace_root / "agent" / "orders"
            cli_plan = json.loads(
                (agent_workspace / "agent_plan.json").read_text(encoding="utf-8")
            )
            spec = load_dataset_spec(agent_workspace / "dataset_spec.yaml")
            advisor_exchange = build_agent_advisor_exchange(agent_workspace)
            mcp_generate = generate_dataset(
                "agent/orders/dataset_spec.yaml",
                "generated",
                output_format="json",
                seed=73,
            )
            generated_folder = workspace_root / "generated"
            manifest = json.loads(
                (generated_folder / "generation_manifest.json").read_text(encoding="utf-8")
            )
            validation_report = json.loads(
                (generated_folder / "validation_report.json").read_text(encoding="utf-8")
            )
            artifact_layout = {
                "files": sorted(
                    path.relative_to(generated_folder).as_posix()
                    for path in generated_folder.rglob("*")
                    if path.is_file()
                )
            }
            with patch.dict(os.environ, {"TRINO_ENABLE_SAFE_SELECT": "false"}):
                trino_mcp = create_trino_mcp(trino_mcp_tools())
            generator_tools = _mcp_tool_contract(generator_mcp)
            trino_tools = _mcp_tool_contract(trino_mcp)
    finally:
        if previous_workspace is None:
            os.environ.pop("TEST_DATA_AGENT_WORKSPACE_ROOT", None)
        else:
            os.environ["TEST_DATA_AGENT_WORKSPACE_ROOT"] = previous_workspace

    fixtures = {
        "advisor-exchange.json": advisor_exchange.model_dump(mode="json"),
        "artifact-layout.json": artifact_layout,
        "cli-agent-plan.json": cli_plan,
        "cli-parser-surface.json": _cli_parser_surface(),
        "contract-catalog.json": _contract_catalog(),
        "dataset-spec.json": spec.model_dump(mode="json"),
        "generation-manifest.json": manifest,
        "mcp-generate.json": mcp_generate,
        "mcp-generator-tools.json": generator_tools,
        "mcp-plan.json": mcp_plan,
        "mcp-trino-tools.json": trino_tools,
        "public-python-api.json": {
            "exports": sorted(test_data_agent.__all__),
        },
        "validation-report.json": validation_report,
    }
    return {
        name: _normalize_contract(payload, workspace_root)
        for name, payload in fixtures.items()
    }


def _contract_catalog() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contracts": {
            "advisor-exchange.json": {
                "version": "1.0",
                "change_rule": "schema_versioned",
            },
            "artifact-layout.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
            "cli-agent-plan.json": {
                "version": "1.0",
                "change_rule": "schema_versioned",
            },
            "cli-parser-surface.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
            "dataset-spec.json": {
                "version": "1.0",
                "change_rule": "schema_versioned",
            },
            "generation-manifest.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
            "mcp-generate.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
            "mcp-generator-tools.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
            "mcp-plan.json": {
                "version": "1.0",
                "change_rule": "schema_versioned",
            },
            "mcp-trino-tools.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
            "public-python-api.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
            "validation-report.json": {
                "version": "1.0",
                "change_rule": "additive_only",
            },
        },
    }


def _mcp_tool_contract(server: Any | None) -> list[dict[str, Any]]:
    if server is None:
        raise RuntimeError("MCP contract generation requires the mcp extra")
    tools = asyncio.run(server.list_tools())
    return [
        {
            "description": tool.description,
            "input_schema": tool.inputSchema,
            "name": tool.name,
            "output_schema": tool.outputSchema,
        }
        for tool in sorted(tools, key=lambda item: item.name)
    ]


def write_contract_fixtures(
    fixtures: Mapping[str, Any],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in CONTRACT_FIXTURE_NAMES:
        payload = fixtures[name]
        output_dir.joinpath(name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _normalize_contract(payload: Any, workspace_root: Path) -> Any:
    if isinstance(payload, dict):
        return {
            key: (
                "<package-version>"
                if key in {"package_version", "generator_algorithm_version"}
                else "<python-version>"
                if key == "python_version"
                else "<dependency-fingerprint>"
                if key in {"dependencies_sha256", "normalized_dependencies_sha256"}
                else {
                    name: "<dependency-version>"
                    for name in sorted(value)
                }
                if key in {"dependencies", "normalized_dependencies"}
                and isinstance(value, dict)
                else _normalize_contract(value, workspace_root)
            )
            for key, value in payload.items()
        }
    if isinstance(payload, list):
        return [_normalize_contract(value, workspace_root) for value in payload]
    if isinstance(payload, str):
        return payload.replace(str(workspace_root), "<workspace>")
    return payload


def _safe_trino_profile() -> dict[str, Any]:
    return {
        "source_type": "trino",
        "table": "orders",
        "row_count": 12,
        "columns": [
            {
                "name": "order_id",
                "data_type": "bigint",
                "approx_distinct_count": 12,
            },
            {
                "name": "status",
                "data_type": "varchar",
                "approx_distinct_count": 2,
                "top_values": [
                    {"value": "paid", "count": 9},
                    {"value": "cancelled", "count": 3},
                ],
            },
            {
                "name": "customer_email",
                "data_type": "varchar",
                "sensitive": True,
                "semantic_type": "email",
                "masked_patterns": [{"pattern": "email", "count": 12}],
            },
        ],
    }


def _cli_parser_surface() -> dict[str, Any]:
    parser = build_parser([])
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    commands: list[str] = []
    aliases: dict[str, str] = {}
    canonical_by_parser: dict[int, str] = {}
    for name, command_parser in subparsers.choices.items():
        parser_id = id(command_parser)
        canonical = canonical_by_parser.get(parser_id)
        if canonical is None:
            canonical_by_parser[parser_id] = name
            commands.append(name)
        else:
            aliases[name] = canonical

    agent_plan = vars(
        parser.parse_args(
            [
                "agent-plan",
                "source.csv",
                "--workspace",
                "workspace",
            ]
        )
    )
    default_names = (
        "source_type",
        "count",
        "seed",
        "output_format",
        "mode",
        "invalid_ratio",
        "table",
        "rule_sample_rows",
        "use_cache",
        "json_output",
    )
    return {
        "schema_version": "1.0",
        "commands": commands,
        "aliases": aliases,
        "agent_plan_defaults": {
            name: agent_plan[name]
            for name in default_names
        },
    }
