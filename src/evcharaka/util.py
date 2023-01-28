"""Collection of functions that represent math behind distance estimation, charge and discharge functions"""
# Formatting
def fractional_hours_human_readable(hours: float) -> str:
    return f"{int(hours):02d}:{int((hours - int(hours)) * 60):02d}"


def hours_human_readable(total_hours: int) -> str:
    days, remainder_total_hours = divmod(total_hours, 24 * 60)
    hours, minutes = divmod(remainder_total_hours, 60)
    text = [
        f"{days: 3d} days" if days else ' ' * 8,
        f"{hours:02d} hr" if hours else ' ' * 5,
        f"{minutes:02d} min" if minutes else ' ' * 6,
    ]
    return ' '.join(text)


# Estimation
def estimate_avg_energy_consumption(distance: float, capacity: float) -> float:
    return (capacity * 1e3) / distance


def estimate_distance(avg_energy_consumption: float, capacity: float) -> float:
    return (capacity * 1e3) / avg_energy_consumption


def estimate_charge(distance: float, avg_energy_consumption: float, capacity: float) -> float:
    return ((distance * avg_energy_consumption) / (capacity * 1e3)) * 100


def estimate_charging_time(
    charger_rating: float,
    from_soc: float,
    to_soc: float,
    capacity: float,
    slow_charge_rate: float,
    fast_charge_rate: float,
    fast_charge: bool=True,
    buffer_time: float = 0.5
) -> float:
    if 0.0 >= from_soc >= to_soc >= 100.0:
        raise ValueError("to_soc must be greater than from_soc")

    if to_soc <= 80.0:
        buffer_time = 0.167

    max_onboard_rate = fast_charge_rate if fast_charge else slow_charge_rate
    charge_rate = min(charger_rating, max_onboard_rate)
    charge_time = ((capacity * ((to_soc - from_soc) / 1e2)) / charge_rate) + buffer_time

    return charge_time


# Actual
def avg_energy_consumption(energy_consumption: list[float]) -> float:
    return sum(energy_consumption) / len(energy_consumption)
