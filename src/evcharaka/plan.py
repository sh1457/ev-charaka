from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from importlib.resources import files
import json
import datetime as dt

import pandas as pd


# Formatting functions
def fractional_hours_human_readable(hours: float) -> str:
    return f"{int(hours):02d}:{int((hours - int(hours)) * 60):02d}"


def hours_human_readable(total_minutes: int) -> str:
    hours, minutes = divmod(total_minutes, 60)
    days, hours = divmod(hours, 24)
    text = [
        f"{days: 3d} days" if days else ' ' * 8,
        f"{hours:02d} hr" if hours else ' ' * 5,
        f"{minutes:02d} min" if minutes else ' ' * 6,
    ]
    return ' '.join(text)


# Estimation functions
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


# Actual functions
def avg_energy_consumption(energy_consumption: list[float]) -> float:
    return sum(energy_consumption) / len(energy_consumption)


# Class definitions
@dataclass
class Entity:
    @classmethod
    def load(cls, key: str) -> Entity:
        search_key_field = cls.__dataclass_fields__.get("search_key", None)

        if search_key_field is None:
            raise ValueError(f"No search key implemented for {cls.__name__!s}")

        if not key:
            raise ValueError(f"No search key provided for {cls.__name__!s}")

        search_terms = [x.strip('{}') for x in search_key_field.default.split(' ')]

        key = key.lower().rsplit(' ', maxsplit=len(search_terms) - 1)

        q = ' and '.join([f"{k}.astype('str').str.lower().str.contains('{v}')" for k, v in zip(search_terms, key)])

        entity_path = f"{cls.__name__.lower()}s.csv"
        path = files('evcharaka.data').joinpath(entity_path)

        df = None
        try:
            with open(path) as fp:
                df = pd.read_csv(fp).query(q, engine='python')

        except Exception as exc:
            print(exc)

        length = df.shape[0]

        if length == 0:
            raise ValueError("No search results")

        if length > 1:
            print(df.values)
            raise ValueError(f"Ambigous search term for search key: {search_key_field.default}")

        obj = cls(**df.iloc[0].to_dict())

        return obj


@dataclass
class Car(Entity):
    make: str
    model: str
    variant: str
    capacity: float
    max_range: float
    exp_range: float
    ac_charge_rate: float
    dc_charge_rate: float
    search_key: str = "{model}"

    @classmethod
    def load(cls, key: str) -> Car:
        return super().load(key)


@dataclass
class Charger(Entity):
    type: str
    charge_rate: float
    search_key: str = "{type} {charge_rate}"

    @classmethod
    def load(cls, key: str) -> Charger:
        return super().load(key)


@dataclass
class DriveParams:
    avg_speed: int
    avg_energy_consumption: int
    daily_start_time: int
    charge_limit: int


@dataclass
class Waypoint:
    name: str
    type: str
    address: str
    distance: float
    duration: int

    @classmethod
    def from_plugshare(cls, data: dict[str,str]) -> Waypoint:
        type_map = {
            "icon-M": "marker",
            "icon-Y": "charger",
        }

        return cls(
            name=data["display"],
            type=type_map.get(data["icon"], "unknown"),
            address=data["address"],
            distance=float(data["distance"].strip().split(' ', maxsplit=1)[0]),
            duration=sum([int(t) * (1 if i-1 == 0 else 60) for i,t in enumerate(reversed(data["duration"].strip().split(' '))) if i%2 == 1]),
        )

    def __str__(self) -> str:
        text = (
            f"[{self.type: >7s}] "
            f"| {self.distance: >7.2f} km "
            f"| {hours_human_readable(self.duration)} "
            f"| {self.name[:40]: >43s}{'...' if len(self.name) > 40 else '   '}"
            "\n"
        )

        return text


@dataclass
class Leg:
    name: str
    gmaps_link: str
    waypoints: list[Waypoint]

    def __str__(self) -> str:
        text = f"{self.name}\n"
        for wp in self.waypoints:
            text += f"|-- {wp!s}"

        text += f"{'- ' * 44}\n"
        text += f"|-- {' ' * 9} | {self.distance: >7.2f} km | {hours_human_readable(self.duration)} |\n"
        text += f"{'- ' * 44}\n"
        return text

    @property
    def distance(self) -> float:
        return sum(map(lambda wp: wp.distance, self.waypoints[:-1]))

    @property
    def duration(self) -> int:
        return sum(map(lambda wp: wp.duration, self.waypoints[:-1]))


@dataclass
class Trip:
    name: str
    legs: list[Leg]

    @classmethod
    def load_trip(cls, path: Path) -> Trip:
        legs = []
        with open(path, "r") as fp:
            for line in fp.readlines():
                leg_data = json.loads(line)
                waypoints = []
                for wp in leg_data["waypoints"]:
                    try:
                        waypoints.append(Waypoint.from_plugshare(wp))
                    except:
                        print(wp)
                        raise
                leg = Leg(name=leg_data["trip_name"], gmaps_link=leg_data["maps_link"], waypoints=waypoints)
                legs.append(leg)

        return cls(name=path.stem, legs=legs)

    def __str__(self) -> str:
        text = f"{self.name}\n"
        for l in self.legs:
            text += '\n'.join(map(lambda x: "|-- " + x, str(l).strip().split("\n"))) + "\n"

        text += f"{'-' * 91}\n"
        text += f"{' ' * 17} | {self.distance: >7.2f} km | {hours_human_readable(self.duration)} |\n"
        text += f"{'-' * 91}\n"

        return text

    @property
    def distance(self) -> float:
        return sum(map(lambda l: l.distance, self.legs))

    @property
    def duration(self) -> int:
        return sum(map(lambda l: l.duration, self.legs))


@dataclass
class Itinerary:
    trip: Trip
    car: Car
    default_charger: Charger
    drive_params: DriveParams
    start_date: dt.datetime | None = dt.datetime.now()
    items: list[ItineraryItem] | None = None

    def plan(self) -> None:
        print("Starting plan")
        print(f"{self.start_date = }")
        print(f"{self.car = }")
        print(f"{self.default_charger = }")
        print(f"{self.drive_params = }")

        ctr = 0
        odometer = 0
        soc = 100.0
        items = []

        for idx, leg in enumerate(self.trip.legs):
            start_datetime = self.start_date + dt.timedelta(days=idx, hours=self.drive_params.daily_start_time)
            print(f"{start_datetime = }")
            current_datetime = start_datetime

            from_details = ItineraryDetail(datetime=current_datetime, name=leg.waypoints[0].name, address=leg.waypoints[0].address, distance=odometer, soc=soc)
            first_item = ItineraryItem(item_id=ctr, details=[from_details])
            items.append(first_item)

            for idx_2, (wp1, wp2) in enumerate(zip(leg.waypoints[:-1], leg.waypoints[1:])):
                details = []
                ctr += 1

                odometer += wp1.distance
                current_datetime += dt.timedelta(minutes=wp1.duration)
                soc -= estimate_charge(distance=wp1.distance, avg_energy_consumption=self.drive_params.avg_energy_consumption, capacity=self.car.capacity)

                if soc < 0:
                    if idx_2:
                        self.items = items
                        raise ValueError("Car will not drive")

                    last_item = items.pop()
                    last_detail = last_item.details[0]

                    charging_duration = estimate_charging_time(car=self.car, charger=Charger.load("ac 3"), from_soc=last_detail.soc, to_soc=100.0)

                    soc += (100.0 - last_detail.soc)
                    current_datetime += dt.timedelta(hours=charging_duration)

                    last_detail.datetime = items[-1].details[-1].datetime + dt.timedelta(hours=charging_duration)
                    last_detail.soc = 100.0

                    items.append(last_item)

                to_details = ItineraryDetail(datetime=current_datetime, name=wp2.name, address=wp2.address, distance=odometer, soc=soc)

                details.append(to_details)

                if wp2.type == "charger":
                    charging_duration = estimate_charging_time(car=self.car, charger=self.default_charger, from_soc=soc, to_soc=self.drive_params.charge_limit)
                    soc = self.drive_params.charge_limit
                    current_datetime += dt.timedelta(hours=charging_duration)

                    charge_details = ItineraryDetail(datetime=current_datetime, name=wp2.name, address=wp2.address, distance=odometer, soc=soc)

                    details.append(charge_details)

                item = ItineraryItem(item_id=ctr, details=details)

                items.append(item)
            ctr += 1

        self.items = items


@dataclass
class ItineraryItem:
    item_id: int
    details: list[ItineraryDetail]

    def __str__(self) -> str:
        text = f"{self.item_id}\n"

        for detail in self.details:
            text += f"|-- {detail!s}"

        return text


@dataclass
class ItineraryDetail:
    datetime: dt.datetime
    name: str
    address: str
    distance: float
    soc: float

    def __str__(self) -> str:
        text = (
            f"[{self.soc: >6.2f}%] "
            f"{self.datetime:%Y-%m-%d %H:%M:%S} "
            f"{self.distance: >7.2f} "
            f"{self.name[:20]}\n"
        )

        return text

def main() -> None:
    vdyut = Car.load("ev max")
    fc = Charger.load("DC 30")
    trip = Trip.load_trip(Path.cwd() / "trips" / "ellora.jsonl")
    drive_params = DriveParams(
        avg_speed = 80.0,
        avg_energy_consumption = 160.0,
        daily_start_time = 9,
        charge_limit = 95,
    )
    itinerary = Itinerary(
        trip = trip,
        car=vdyut,
        default_charger=fc,
        drive_params=drive_params,
        start_date=dt.datetime(2022, 12, 16),
    )

    try:
        itinerary.plan()
    except ValueError as exc:
        # raise
        pass

    details = [detail for item in itinerary.items for detail in item.details]

    df = pd.DataFrame(data=details, columns=list(ItineraryDetail.__dataclass_fields__.keys()))

    print(df.head())

if __name__ == '__main__':
    main()
