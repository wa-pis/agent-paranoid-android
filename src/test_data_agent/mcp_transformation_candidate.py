"""Unregistered workspace execution candidate; fictional test use only.

No production tool registration or approval issuer. Public activation requires the
completed wiring's independent safety review and matching policy amendments.
"""

from typing import Any

from test_data_agent.core.limits import (
    DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, GenerationBudget,
)
from test_data_agent.io.transformation_publish import _execute_reviewed_test_from_paths
from test_data_agent.mcp_generator_server import resolve_workspace_path


def _create_test_candidate_mcp() -> Any | None:
    """Fictional test composition only; production registration is unchanged."""
    from test_data_agent.mcp_generator_transport import create_generator_mcp
    from test_data_agent.trino_work_budget import (
        DEFAULT_QUERY_WORK_LIMITS, QueryWorkBudget, with_query_work_budget,
    )

    def request_budget() -> QueryWorkBudget | None:
        if server is None:
            return None
        try:
            request = server.get_context().request_context.request
        except (LookupError, ValueError):
            return None
        return request if isinstance(request, QueryWorkBudget) else None

    server = create_generator_mcp([
        with_query_work_budget(_execute_candidate_transformation, DEFAULT_QUERY_WORK_LIMITS,
                               budget_provider=request_budget),
    ])
    return server


def _execute_candidate_transformation(
    input_path: str, policy_path: str, output_path: str, snapshot_sha256: str,
    *, table_name: str | None = None, receipt_path: str | None = None,
    max_output_bytes: int | None = None,
    max_total_input_bytes: int | None = None,
) -> dict[str, object]:
    """Consume existing approval only; never return rows or create receipts."""
    source = resolve_workspace_path(input_path, must_exist=True, expect_file=True)
    policy = resolve_workspace_path(policy_path, must_exist=True, expect_file=True)
    destination = resolve_workspace_path(output_path, expect_directory=True)
    receipt = (resolve_workspace_path(receipt_path, must_exist=True, expect_file=True)
               if receipt_path is not None else None)
    return _execute_reviewed_test_from_paths(
        source, table_name or source.stem, policy, destination,
        expected_snapshot_sha256=snapshot_sha256,
        max_total_bytes=max_total_input_bytes,
        max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES,
        max_output_bytes=max_output_bytes, budget=GenerationBudget(), receipt_path=receipt,
    )
