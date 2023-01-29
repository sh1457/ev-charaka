import pytest

from evcharaka.plan import *


@pytest.fixture
def nexon_ev_max() -> Car:
    return Car.load("ev max")


@pytest.fixture
def ac_3() -> Charger:
    return Charger.load("ac 3")


@pytest.fixture
def dc_25() -> Charger:
    return Charger.load("dc 25")


@pytest.fixture
def dc_30() -> Charger:
    return Charger.load("dc 30")