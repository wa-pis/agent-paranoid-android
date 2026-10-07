"""Unregistered workspace execution candidate; fictional test use only.

No production tool registration or approval issuer. Public activation requires the
completed wiring's independent safety review and matching policy amendments.
"""

from typing import Any, Literal, TYPE_CHECKING
from pathlib import Path
from collections.abc import Mapping
from test_data_agent.io.transformation_batch_profile import BatchProfile
from test_data_agent.io.transformation_query_workflow import _ConfiguredQueryReference
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from test_data_agent.core.limits import (
    DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, GenerationBudget,
)
from test_data_agent.io.transformation_publish import _execute_reviewed_test_from_paths, TransformationCleanupError
from test_data_agent.trino_work_budget import QueryWorkBudget, current_query_work_budget

if TYPE_CHECKING:
    from test_data_agent.io.transformation_query_sessions import _ConfiguredQuerySessions


class _McpTransformationBudget(GenerationBudget):
    """Check both deadlines at the existing transformation work checkpoints."""

    def __init__(self, request_budget: QueryWorkBudget | None) -> None:
        super().__init__()
        self._request_budget = request_budget

    def check(self, stage: str) -> None:
        if self._request_budget is not None:
            self._request_budget.check_invocation_deadline()
        super().check(stage)


@contextmanager
def _mcp_transformation_budget() -> Iterator[GenerationBudget]:
    budget = _McpTransformationBudget(current_query_work_budget())
    try:
        yield budget
    except TransformationCleanupError:
        raise
    except ValueError:
        # Private parsers detach ValueError failures. Recheck the same monotonic
        # deadlines at the adapter boundary to retain safe typed limit errors.
        budget.check("MCP transformation failure")
        raise


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
    with _mcp_transformation_budget() as budget:
        return _execute_reviewed_test_from_paths(
            source, table_name or source.stem, policy, destination,
            expected_snapshot_sha256=snapshot_sha256,
            max_total_bytes=max_total_input_bytes,
            max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES,
            max_output_bytes=max_output_bytes, budget=budget, receipt_path=receipt,
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
        with _mcp_transformation_budget() as budget:
            return run_batch_workflow(request, budget=budget).metadata()

    return common_transformation


@contextmanager
def _configured_query_tools(root: Path, profile: BatchProfile, *, references: Mapping[str, _ConfiguredQueryReference],
        max_total_bytes: int, max_review_bytes: int) -> Iterator[Callable[..., dict[str, object]]]:
    """Closed server-owned preparation; review/execute never reconnect."""
    from test_data_agent.io.transformation_query_workflow import _temporary_configured_query_profile
    from test_data_agent.mcp_generator_server import resolve_workspace_path

    root = resolve_workspace_path(str(root), must_exist=True, expect_directory=True)
    with _mcp_transformation_budget() as budget:
        with _temporary_configured_query_profile(root, profile, references=references,
                max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
                budget=budget) as (captured_root, _):
            yield _common_batch_tool(captured_root)



def _configured_query_session_tool(sessions: "_ConfiguredQuerySessions") -> Callable[..., dict[str, object]]:
    """Closed server-injected session consumer; MCP never issues local approval."""
    from test_data_agent.io.transformation_batch import TransformationBatchError
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.trino_work_budget import QueryWorkBudgetExceeded

    def configured_query_session(operation: Literal["open", "review", "validate", "execute", "close"],
            handle: str | None = None, profile: str | None = None, references: str | None = None,
            snapshot_sha256: str | None = None, destination: str | None = None,
            max_total_bytes: int | None = None, max_review_bytes: int | None = None,
            max_output_bytes: int | None = None) -> dict[str, object]:
        try:
            if operation == "open":
                if (profile is None or references is None or handle is not None
                        or snapshot_sha256 is not None or destination is not None
                        or max_total_bytes is None or max_review_bytes is None or max_output_bytes is None):
                    raise ValueError
                return sessions.open(profile, references, max_total_bytes=max_total_bytes,
                    max_review_bytes=max_review_bytes, max_output_bytes=max_output_bytes)
            if (handle is None or profile is not None or references is not None
                    or any(value is not None for value in (max_total_bytes, max_review_bytes, max_output_bytes))):
                raise ValueError
            return sessions.consume(handle, operation, snapshot_sha256=snapshot_sha256, destination=destination)
        except (TransformationLimitError, TransformationCleanupError, QueryWorkBudgetExceeded):
            raise
        except Exception:
            sessions.refuse(handle)
            raise TransformationBatchError("invalid SQL session request") from None

    return configured_query_session



def _approve_configured_query_session_locally(sessions: "_ConfiguredQuerySessions", handle: str) -> int:
    """Owning server's local console/UI action; this callable is NEVER an MCP tool.

    Local operator supplies the opaque handle shown by review. The existing CLI
    approval handler resolves the owned batch and obtains controlling-TTY consent.
    After it returns, remote validate/execute can consume that exact receipt.
    """
    from test_data_agent.cli_transformation_candidate import _candidate_batch_approve_main
    return _candidate_batch_approve_main(sessions.local_approval_arguments(handle))



@contextmanager
def _configured_query_session_server(root: Path, *, max_active: int,
        max_cumulative_bytes: int, max_seconds: float) -> Iterator[Any | None]:
    """Closed boot composition: one bounded session owner for one MCP server.

    Keep this context around the server run; finally closes every owned capture.
    A local console may use the returned tools' handoff descriptor with existing
    CLI approve; approval issuance is never registered as an MCP tool.
    """
    from test_data_agent.io.transformation_query_sessions import _ConfiguredQuerySessions
    from test_data_agent.mcp_generator_transport import create_generator_mcp

    sessions = _ConfiguredQuerySessions(root, max_active=max_active,
        max_cumulative_bytes=max_cumulative_bytes, max_seconds=max_seconds)
    try:
        yield create_generator_mcp([_configured_query_session_tool(sessions)], strict_arguments=True)
    finally:
        sessions.close()
