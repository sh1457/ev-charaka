from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from importlib.resources import files
import json
import datetime as dt

import pandas as pd


# Formatting
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
    drive_params: DriveParams
    start_date: dt.datetime | None = dt.datetime.now()
