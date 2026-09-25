"""Interactive policy editing only; never approval or source-row execution."""

import json
import os
from pathlib import Path
import select
import time
from typing import TextIO

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_approval import ApprovalRequest
from test_data_agent.core.transformation_policy import BehaviorPolicyError, parse_behavior_policy
from test_data_agent.core.transformation_yaml import dump_behavior_policy_yaml, load_behavior_policy_yaml
from test_data_agent.io.behavior_policy_files import save_behavior_policy_file
from test_data_agent.io.transformation_source import prepare_csv_review_from_paths, prepare_csv_review_request


def _answer(input_fd: int, output: TextIO, prompt: str) -> str:
    output.write(prompt)
    output.flush()
    deadline = time.monotonic() + 60
    answer = bytearray()
    while len(answer) < 32:
        if not select.select([input_fd], [], [], max(0, deadline - time.monotonic()))[0]:
            break
        byte = os.read(input_fd, 1)
        if not byte:
            break
        if byte == b"\n":
            return answer.decode("ascii").rstrip("\r")
        answer.extend(byte)
    raise ValueError("invalid decision input")


def edit_csv_policy_decisions(
    source_path: Path, table_name: str, policy_path: Path, *,
    input_stream: TextIO, output_stream: TextIO,
    max_total_bytes: int, max_review_bytes: int, budget: GenerationBudget,
) -> ApprovalRequest:
    """Save explicit decisions in place, preserving all actions and references."""
    try:
        if not input_stream.isatty() or not output_stream.isatty():
            raise ValueError
        root = policy_path.parent.absolute()
        original = prepare_csv_review_from_paths(
            source_path, table_name, root, policy_path.name,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget,
        )
        policy_bytes = next(part.payload for part in original.parts if part.kind == "policy")
        policy = load_behavior_policy_yaml(policy_bytes, max_bytes=max_total_bytes, budget=budget)
        payload = policy.model_dump(mode="json")
        review = json.loads(original.review)
        output_stream.write("Edit sensitivity decisions only. Actions stay unchanged; this is not approval.\n")
        for decision, field in zip(payload["fields"], review["fields"], strict=True):
            budget.check("policy decision wizard")
            output_stream.write(json.dumps(field, ensure_ascii=True, indent=2) + "\n")
            answer = _answer(input_stream.fileno(), output_stream,
                             "Decision [sensitive/non_sensitive/unknown]: ")
            if answer not in {"sensitive", "non_sensitive", "unknown"}:
                raise ValueError
            decision["sensitivity"] = answer
        revised = parse_behavior_policy(payload)
        revised_bytes = dump_behavior_policy_yaml(revised, max_bytes=max_total_bytes, budget=budget)
        source = next(part for part in original.parts if part.kind == "source")
        references = tuple(part for part in original.parts if part.kind in {"mapping", "generation_policy"})
        updated = prepare_csv_review_request(
            revised_bytes, source, references, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, budget=budget,
        )
        output_stream.write(updated.review.decode("ascii") + "\n")
        if _answer(input_stream.fileno(), output_stream,
                   "Type SAVE to replace the policy (not approval): ") != "SAVE":
            raise ValueError
        current = prepare_csv_review_from_paths(
            source_path, table_name, root, policy_path.name,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget,
        )
        if current != original:
            raise ValueError
        save_behavior_policy_file(root, policy_path.name, revised, max_bytes=max_total_bytes, budget=budget)
        return updated
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    try:
        raise BehaviorPolicyError("policy decisions not saved; invalid input, conflict or changed snapshot")
    except BehaviorPolicyError as error:
        error.__context__ = None
        raise
