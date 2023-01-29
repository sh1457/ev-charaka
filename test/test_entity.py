"""Collection of entities that model cars, chargers and trips"""
import pytest

from evcharaka.entity import *


@pytest.mark.parametrize(
    "hours,expected",
    [
        pytest.param(1.5 , "01:30", id="simple fraction > 1"),
        pytest.param(0.75, "00:45", id="simple fraction < 1"),
        pytest.param(3   , "03:00", id="simple integer > 1"),
    ]
)
def test_fractional_hours_human_readable(hours: float, expected: str) -> None:
    assert fractional_hours_human_readable(hours) == expected


@pytest.mark.parametrize(
    "minutes,expected",
    [
        pytest.param(60  , "01 hr", id="simple integer // 60"),
        pytest.param(720 , "12 hr", id="simple integer > 60"),
        pytest.param(1441, "1 days       01 min", id="simple integer > 1440"),
        pytest.param(7200, "5 days", id="simple integer // 1440"),
    ]
)
def test_hours_human_readable(minutes: int, expected: str) -> None:
    assert hours_human_readable(minutes).strip() == expected
