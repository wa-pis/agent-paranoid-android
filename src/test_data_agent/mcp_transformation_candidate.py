"""Unregistered workspace execution candidate; fictional test use only.

No production tool registration or approval issuer. Public activation requires the
completed wiring's independent safety review and matching policy amendments.
"""

from typing import Any, Literal
from pathlib import Path
from collections.abc import Callable

from test_data_agent.core.limits import (
    DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, GenerationBudget,
)
from test_data_agent.io.transformation_publish import _execute_reviewed_test_from_paths


def _create_test_candidate_mcp(*, prospective: bool = False) -> Any | None:
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

    consumer = with_query_work_budget(_execute_candidate_transformation, DEFAULT_QUERY_WORK_LIMITS,
                                     budget_provider=request_budget)
    if prospective:
        # Rename only this fresh wrapper; never mutate the shared application callable.
        consumer.__name__ = "execute_transformation"
    server = create_generator_mcp([consumer])
    return server


def _execute_candidate_transformation(
    input_path: str, policy_path: str, output_path: str, snapshot_sha256: str,
    *, table_name: str | None = None, receipt_path: str | None = None,
    max_output_bytes: int | None = None,
    max_total_input_bytes: int | None = None,
) -> dict[str, object]:
    """Consume existing approval only; never return rows or create receipts."""
    from test_data_agent.mcp_generator_server import resolve_workspace_path

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


def _create_test_batch_mcp(root: Path) -> Any | None:
    """Isolated common consumer server with trusted fixed root; no issuer."""
    from test_data_agent.mcp_generator_transport import create_generator_mcp

    return create_generator_mcp([_common_batch_tool(root)], strict_arguments=True)


def _common_batch_tool(root: Path) -> Callable[..., dict[str, object]]:
    """Closed callable for prospective composition; root is server-owned."""
    from test_data_agent.io.transformation_batch_workflow import BatchWorkflowRequest, run_batch_workflow

    def common_transformation(operation: Literal["review", "validate", "execute"], profile: str,
                              max_total_bytes: int, max_review_bytes: int, max_output_bytes: int,
                              snapshot_sha256: str | None = None, receipt: str | None = None,
                              destination: str | None = None
                              ) -> dict[str, object]:
        """Closed fictional common-profile consumer; no rows or approval issuer."""
        request = BatchWorkflowRequest(operation=operation, root=root, profile=profile,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
            max_output_bytes=max_output_bytes, snapshot_sha256=snapshot_sha256, receipt=receipt,
            destination=destination)
        return run_batch_workflow(request, budget=GenerationBudget()).metadata()

    return common_transformation
