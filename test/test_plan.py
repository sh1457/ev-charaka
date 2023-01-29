from contextlib import nullcontext
from unittest.mock import Mock
import pytest

from evcharaka.plan import *


@pytest.mark.parametrize(
    "distance,capacity,expected",
    [
        pytest.param(100, 40  , 400, id="simple integers"),
        pytest.param(100, 40.5, 405, id="simple fractions"),
    ]
)
def test_estimate_avg_energy_consumption(distance: float, capacity: float, expected: float) -> None:
    assert estimate_avg_energy_consumption(distance, capacity) == expected

@pytest.mark.parametrize(
    "consumption,capacity,expected",
    [
        pytest.param(100, 40  , 400, id="simple integers"),
        pytest.param(100, 40.5, 405, id="simple fractions"),
    ]
)
def test_estimate_distance(consumption: float, capacity: float, expected: float) -> None:
    assert estimate_distance(consumption, capacity) == expected


@pytest.mark.parametrize(
    "distance,consumption,capacity,expected",
    [
        pytest.param(100, 100, 40  , 25, id="simple integers"),
        pytest.param(100, 100, 40.5, 24.69, id="simple fractions"),
    ]
)
def test_estimate_charge(distance: float, consumption: float, capacity: float, expected: float) -> None:
    assert estimate_charge(distance, consumption, capacity) == pytest.approx(expected)

@pytest.mark.parametrize(
    "car,charger,from_soc,to_soc,expected,error",
    [
        pytest.param("nexon_ev_max", "ac_3", 40, 80, 4.91, nullcontext(), id="ac charging small"),
        pytest.param("nexon_ev_max", "ac_3", 20, 90, 8.59, nullcontext(), id="ac charging large"),
        pytest.param("nexon_ev_max", "ac_3", 20, 100, 10.32, nullcontext(), id="ac charging full"),
        pytest.param("nexon_ev_max", "dc_30", 20, 90, 0.94, nullcontext(), id="dc charging"),
        pytest.param("nexon_ev_max", "dc_30", 20, 120, Mock(), pytest.raises(ValueError, match="to_soc must be greater than from_soc"), id="raise exception"),
    ]
)
def test_estimate_charging_time(request, car: Car, charger: Charger, from_soc: float, to_soc: float, expected: float, error) -> None:
    with error:
        assert estimate_charging_time(
            request.getfixturevalue(car),
            request.getfixturevalue(charger),
            from_soc,
            to_soc
        ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "consumptions,expected",
    [
        pytest.param([100, 100, 100], 100, id="same integers"),
        pytest.param([110, 100, 90] , 100, id="diff integers"),
    ]
)
def test_avg_energy_consumption(consumptions: list[float], expected: float) -> None:
    assert avg_energy_consumption(consumptions) == expected


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
