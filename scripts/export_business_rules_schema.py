#!/usr/bin/env python3
"""Export the standalone BusinessRules JSON Schema from its runtime model."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from test_data_agent.rules.models import BusinessRules  # noqa: E402

DEFAULT_OUTPUT = ROOT / "schemas" / "business_rules.schema.json"


def build_business_rules_schema() -> dict[str, Any]:
    schema = BusinessRules.model_json_schema(ref_template="#/$defs/{model}")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://github.com/wa-pis/agent-paranoid-android/schemas/business_rules.schema.json"
    return schema


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    output = Path(args[0]) if args else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_business_rules_schema(), indent=2, sort_keys=True) + "\n")
    print(f"Wrote business rules schema: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
