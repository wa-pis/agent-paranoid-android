"""Regenerate checked-in public contract fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path

from contract_fixtures import (
    build_contract_fixtures,
    write_contract_fixtures,
)


def main() -> int:
    output_dir = Path("tests/fixtures/contracts")
    with tempfile.TemporaryDirectory(prefix="test-data-agent-contracts-") as temp:
        fixtures = build_contract_fixtures(Path(temp))
    write_contract_fixtures(fixtures, output_dir)
    print(f"Wrote {len(fixtures)} contract fixtures to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
