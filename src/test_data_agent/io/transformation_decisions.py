"""Interactive policy editing only; never approval or source-row execution."""

import json
import os
from pathlib import Path
import select
import time
from typing import TextIO

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.serialization import load_limited_json
from test_data_agent.core.transformation_approval import ApprovalRequest
from test_data_agent.core.transformation_policy import BehaviorPolicyError, parse_behavior_policy
from test_data_agent.core.transformation_yaml import dump_behavior_policy_yaml, load_behavior_policy_yaml
from test_data_agent.io.behavior_policy_files import save_behavior_policy_file
from test_data_agent.io.transformation_source import (
    load_policy_references, prepare_csv_review_from_paths, prepare_csv_review_request,
)


def _answer(input_fd: int, output: TextIO, prompt: str, *, max_bytes: int = 32) -> str:
    output.write(prompt)
    output.flush()
    deadline = time.monotonic() + 60
    answer = bytearray()
    while len(answer) < max_bytes:
        if not select.select([input_fd], [], [], max(0, deadline - time.monotonic()))[0]:
            break
        byte = os.read(input_fd, 1)
        if not byte:
            break
        if byte == b"\n":
            return answer.decode("utf-8").rstrip("\r")
        answer.extend(byte)
    raise ValueError("invalid decision input")


def _private_answer(input_fd: int, output: TextIO, prompt: str) -> str:
    # Keep noninteractive CLI imports portable; private terminal entry is POSIX-only.
    import termios

    try:
        previous = termios.tcgetattr(input_fd)
        hidden = previous.copy()
        hidden[3] &= ~termios.ECHO
        try:
            termios.tcsetattr(input_fd, termios.TCSANOW, hidden)
            return _answer(input_fd, output, prompt, max_bytes=4096)
        finally:
            termios.tcsetattr(input_fd, termios.TCSANOW, previous)
            output.write("\n")
            output.flush()
    except termios.error:
        raise ValueError("private terminal input unavailable") from None


def _action(input_fd: int, output: TextIO, *, unmatched: bool = False) -> dict[str, object] | None:
    options = "reject/preserve/synthesize" if unmatched else "keep/drop/preserve/synthesize/substitute/replace_text/derive"
    selected = _answer(input_fd, output, f"{'Unmatched' if unmatched else 'Action'} [{options}]: ")
    if selected not in options.split("/"):
        raise ValueError
    if selected == "keep":
        return None
    result: dict[str, object] = {"action": selected}
    if selected == "preserve":
        result["authorization_ref"] = _private_answer(input_fd, output, "Authorization reference (hidden): ")
        result["comment"] = _private_answer(input_fd, output, "Preservation comment (hidden): ")
    elif selected == "synthesize":
        result["generation_policy_ref"] = _private_answer(input_fd, output, "Generation policy path (hidden): ")
    elif selected == "derive":
        result["expression"] = _private_answer(input_fd, output, "Expression (hidden): ")
        result["dependencies"] = load_limited_json(
            _private_answer(input_fd, output, "Dependency names JSON (hidden): "),
        )
    elif selected in {"substitute", "replace_text"}:
        result["mapping"] = load_limited_json(_private_answer(input_fd, output, "Mapping JSON (hidden): "))
        result["unmatched"] = _action(input_fd, output, unmatched=True)
    return result


def edit_csv_policy_decisions(
    source_path: Path, table_name: str, policy_path: Path, *,
    input_stream: TextIO, output_stream: TextIO,
    max_total_bytes: int, max_review_bytes: int, budget: GenerationBudget,
    edit_actions: bool = False,
) -> ApprovalRequest:
    """Save explicit decisions; edit actions only when separately requested."""
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
        output_stream.write("Edit policy decisions; this is not approval.\n" if edit_actions else
                            "Edit sensitivity decisions only. Actions stay unchanged; this is not approval.\n")
        for decision, field in zip(payload["fields"], review["fields"], strict=True):
            budget.check("policy decision wizard")
            output_stream.write(json.dumps(field, ensure_ascii=True, indent=2) + "\n")
            answer = _answer(input_stream.fileno(), output_stream,
                             "Decision [sensitive/non_sensitive/unknown]: ")
            if answer not in {"sensitive", "non_sensitive", "unknown"}:
                raise ValueError
            decision["sensitivity"] = answer
            if edit_actions:
                action = _action(input_stream.fileno(), output_stream)
                if action is not None:
                    decision["behavior"] = action
        revised = parse_behavior_policy(payload)
        revised_bytes = dump_behavior_policy_yaml(revised, max_bytes=max_total_bytes, budget=budget)
        source = next(part for part in original.parts if part.kind == "source")
        reference_limit = max_total_bytes - len(revised_bytes) - len(source.payload)
        references = load_policy_references(revised, root, max_bytes=reference_limit, budget=budget)
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
        if load_policy_references(revised, root, max_bytes=reference_limit, budget=budget) != references:
            raise ValueError
        save_behavior_policy_file(root, policy_path.name, revised, max_bytes=max_total_bytes, budget=budget)
        return updated
    except (OSError, ValueError, TypeError, AttributeError, ImportError):
        pass
    try:
        raise BehaviorPolicyError("policy decisions not saved; invalid input, conflict or changed snapshot")
    except BehaviorPolicyError as error:
        error.__context__ = None
        raise
