"""Fictional extreme intervals expose rounding outside reviewed temporal bounds."""
from datetime import date, datetime
import random

import pytest

from test_data_agent.core.distribution import DateRangeDistribution, DateTimeRangeDistribution
from test_data_agent.generation.entity_generator import ranged_datetime


class EndpointRandom(random.Random):
    def __init__(self, upper):
        super().__init__(0)
        self.upper = upper
    def randint(self, low, high):
        return high if self.upper else low


@pytest.mark.parametrize("timezone", ["", "+03:00", "-07:00"])
@pytest.mark.parametrize("upper", [False, True])
def test_long_fractional_datetime_interval_never_exceeds_maximum(timezone, upper):
    bounds = DateTimeRangeDistribution(
        min=f"1000-01-01T00:00:00{timezone}",
        max=f"3000-01-01T00:00:00.999999{timezone}",
    )
    value = datetime.fromisoformat(ranged_datetime(bounds, {}, EndpointRandom(upper), False))
    assert datetime.fromisoformat(bounds.min) <= value <= datetime.fromisoformat(bounds.max)


@pytest.mark.parametrize("low,high", [
    ("2031-01-01T00:00:00", "2031-01-01T00:00:00.999999"),
    ("2031-01-01T00:00:00.750000", "2031-01-01T00:00:01.749999"),
    ("2031-01-01T00:00:00+03:00", "2031-01-01T00:00:01+03:00"),
    ("2031-01-01T00:00:00+03:00", "2031-01-01T00:00:00+02:00"),
])
def test_short_offset_and_subsecond_intervals_preserve_whole_second_policy(low, high):
    bounds = DateTimeRangeDistribution(min=low, max=high)
    value = datetime.fromisoformat(ranged_datetime(bounds, {}, EndpointRandom(True), False))
    lower, higher = datetime.fromisoformat(low), datetime.fromisoformat(high)
    assert lower <= value <= higher
    assert value.microsecond == lower.microsecond


@pytest.mark.parametrize("upper", [False, True])
def test_extreme_date_interval_keeps_endpoints(upper):
    bounds = DateRangeDistribution(min="0001-01-01", max="9999-12-31")
    value = date.fromisoformat(ranged_datetime(bounds, {}, EndpointRandom(upper), True))
    assert value == date.fromisoformat(bounds.max if upper else bounds.min)


@pytest.mark.parametrize("distribution_type", [DateRangeDistribution, DateTimeRangeDistribution])
@pytest.mark.parametrize("endpoint", [{"max": "2010-01-01"}, {"min": "2030-01-01"}])
def test_partial_bounds_conflicting_with_fallback_reject(distribution_type, endpoint):
    bounds = distribution_type(**endpoint)
    with pytest.raises(ValueError, match="effective minimum exceeds maximum"):
        ranged_datetime(bounds, {}, EndpointRandom(True), distribution_type is DateRangeDistribution)


@pytest.mark.parametrize("data_type,kind", [("date", "date_range"), ("datetime", "datetime_range")])
def test_conflicting_fallback_cannot_replace_a_published_dataset(tmp_path, capsys, data_type, kind):
    import json
    from test_data_agent.cli import main
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"entities": [{"name": "events", "row_count": 2,
        "fields": [{"name": "observed_at", "data_type": data_type,
                    "distribution": {"kind": kind, "max": "2010-01-01"}}]}]}))
    output = tmp_path / "output"
    output.mkdir()
    previous = output / "events.csv"
    previous.write_text("fictional-previous-output")
    assert main(["--json", "generate", str(spec), "--output", str(output), "--overwrite"]) != 0
    assert previous.read_text() == "fictional-previous-output"
    assert not (output / "generation_manifest.json").exists()
    assert "effective minimum exceeds maximum" in capsys.readouterr().out
