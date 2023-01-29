"""Collection of functions that represent math behind distance estimation, charge and discharge functions"""
from evcharaka.entity import Car, Charger


# Estimation
def estimate_avg_energy_consumption(distance: float, capacity: float) -> float:
    return (capacity * 1e3) / distance


def estimate_distance(avg_energy_consumption: float, capacity: float) -> float:
    return (capacity * 1e3) / avg_energy_consumption


def estimate_charge(distance: float, avg_energy_consumption: float, capacity: float) -> float:
    return round((distance * avg_energy_consumption) / (capacity * 1e3), 4) * 100


def estimate_charging_time(car: Car, charger: Charger, from_soc: float, to_soc: float) -> float:
    if not (100 >= to_soc >= 0 and 100 >= from_soc >= 0 and to_soc >= from_soc):
        raise ValueError("to_soc must be greater than from_soc")

    buffer_time = 0 if to_soc <= 95 else 0.5
    max_onboard_rate = car.dc_charge_rate if charger.type == "DC" else car.ac_charge_rate
    charge_rate = min(charger.charge_rate, max_onboard_rate)

    charge_time = ((car.capacity * ((to_soc - from_soc) / 1e2)) / charge_rate) + buffer_time

    return round(charge_time, 2)


# Actual
def avg_energy_consumption(energy_consumption: list[float]) -> float:
    return sum(energy_consumption) / len(energy_consumption)
