import json
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from geopy.distance import geodesic
import requests
import os
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()  # reads .env and puts its values into os.environ

APP_KEY = os.environ.get("TFL_APP_KEY")

logger = logging.getLogger(__name__)

BASE_URL = "https://api.tfl.gov.uk"

"""Opening the NAPTAN json to avoid constantly reopening it"""
with (Path(__file__).with_name("naptan.json")).open(encoding="utf-8") as f:
    NAPTAN = json.load(f)

def normalize_station_name(name):
    return name.replace("’", "'").casefold().strip()

STATION_NAMES = {s["naptanID"]: s["commonName"] for s in NAPTAN}
STATION_IDS = {normalize_station_name(s["commonName"]): s["naptanID"] for s in NAPTAN}
EST_MAX_TRAIN_SPEED = 60 # tfl says that trains can reach about 60 mph

SESSION = requests.Session()
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4, backoff_factor=1,
    status_forcelist=[429, 502, 503, 504],
    respect_retry_after_header=True,
)))
APP_KEY = os.environ.get("TFL_APP_KEY")

class Train:
    def __init__(self):
        self.line = ""
        self.direction = ""
        self.vehicle_id = ""
        self.stops = []

class Route:
    def __init__(self, station, current_time):
        self.station = station
        self.current_time = current_time

        self.current_trains = []
        self.trains = []
        self.available_stations = {}

        self.parent = None
        self.total_time = current_time
        self.heuristic = 0
        self.f_score = 0

        self.route_complete = False

def route_stations(route):
    """Return the ordered station path by walking back through parent routes."""
    stations = []
    current = route
    while current is not None:
        stations.append(current.station)
        current = current.parent
    return list(reversed(stations))


def station_label(naptan_id):
    """Human-readable station name for a NaPTAN ID."""
    name = STATION_NAMES.get(naptan_id, naptan_id)
    return name.removesuffix(" Underground Station")


def route_times(route):
    """Minutes from the search start at each station on the route, in path order."""
    times = []
    current = route
    while current is not None:
        times.append(current.current_time)
        current = current.parent
    return list(reversed(times))


def format_route(route, start_time):
    """Return a readable, leg-by-leg description of a completed route, with times."""
    stations = route_stations(route)
    times = route_times(route)

    def clock(minutes):
        return (start_time + timedelta(minutes=minutes)).astimezone().strftime("%H:%M")

    # route.trains[i] is the train used to get from stations[i] to stations[i + 1].
    # Consecutive hops on the same vehicle are merged into one leg.
    legs = []
    for i, train in enumerate(route.trains):
        if legs and legs[-1]["vehicle_id"] == train.vehicle_id:
            legs[-1]["to"] = stations[i + 1]
            legs[-1]["arrive"] = times[i + 1]
        else:
            legs.append({
                "line": train.line,
                "vehicle_id": train.vehicle_id,
                "from": stations[i],
                "to": stations[i + 1],
                "depart": times[i],
                "arrive": times[i + 1],
            })

    lines = [
        f"{station_label(stations[0])} → {station_label(stations[-1])}"
        f"  (about {route.current_time} min, arriving {clock(route.current_time)})",
        "",
    ]
    for n, leg in enumerate(legs, start=1):
        if n > 1:
            lines.append(f"   Change at {station_label(leg['from'])}")
        lines.append(
            f"{n}. {leg['line']} line: "
            f"{clock(leg['depart'])} {station_label(leg['from'])} → "
            f"{clock(leg['arrive'])} {station_label(leg['to'])}"
        )
    return "\n".join(lines)


def get_json(path):
    params = {"app_key": APP_KEY} if APP_KEY else None
    response = SESSION.get(f"{BASE_URL}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()

""" Fetches the stations long and lats from a csv file
    Converts fetched values from file and returns
    a dictionary of station NapTans and their lons and lats
    {String: (float,float)}
    """
def get_stations_lon_lat_dictionary(
    station_coord_csv=Path(__file__).resolve().parent.parent
    / "tfl-stationdata-detailed"
    / "StationPoints.csv",
):
    # load the csv file
    points = pd.read_csv(station_coord_csv)

    # filter for tube stations using NapTan
    tube_points = points[points["StationUniqueId"].str.startswith("940GZZLU", na=False)]

    # remove duplicates
    unique_points = tube_points.drop_duplicates(subset=["StationUniqueId"])

    # convert to dictionary
    coord_dict = {}
    for _, row in unique_points.iterrows():
        naptan = row["StationUniqueId"]
        lat = row["Lat"]
        lon = row["Lon"]
        coord_dict[naptan] = (lat,lon)

    return coord_dict

def get_station_id(station):
    # Allow NAPTAN IDs directly.
    station_str = str(station)
    if station_str.upper().startswith("9"):
        return station_str.upper()

    lookup_keys = (
        normalize_station_name(station_str),
        normalize_station_name(f"{station_str} Underground Station"),
    )
    for key in lookup_keys:
        station_id = STATION_IDS.get(key)
        if station_id:
            return station_id
    raise ValueError(f"Station not found: {station}")


def get_vehicle_predictions(
    vehicle_ids,
):  # some trains have vehicle ids that track their jouneys(not all). this function gets the timetable for those trains
    predictions = []
    for i in range(0, len(vehicle_ids), 25):
        ids = ",".join(vehicle_ids[i : i + 25])
        data = get_json(f"/Vehicle/{ids}/Arrivals")
        predictions.extend(data)
    return predictions


def calculate_times(start_time, scheduled, live):  # combines live predictions and timetables
    result = {}
    for station, scheduled_time in scheduled.items():
        if station in live:
            arrival = live[station]
        else:
            arrival = scheduled_time
            result[station] = round((arrival - start_time).total_seconds() / 60)
    return result


def get_station_order(timetable):
    route_data = timetable["timetable"]["routes"][0]
    station_groups = []
    for interval_group in route_data["stationIntervals"]:
        stations = []
        for interval in interval_group["intervals"]:
            station_id = interval["stopId"]
            if station_id in STATION_NAMES:
                stations.append((station_id, interval["timeToArrival"]))
        station_groups.append(stations)
    return station_groups


@lru_cache(maxsize=None)
def get_timetable(line_id, from_id, to_id):
    """Fetch a line timetable once. Returns None if TfL has no valid timetable for this combination."""
    try:
        return get_json(f"/Line/{line_id}/Timetable/{from_id}/to/{to_id}")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            raise  # rate limited: don't cache a failure for a combination that may be valid
        return None  # 404/500: cache the failure so we don't ask again


def get_trains(station, start_time, arrival_time, minutes=30):
    station_id = get_station_id(station)
    logger.debug("Fetching arrivals for %s", station_id)
    end_time = arrival_time + timedelta(minutes=minutes)
    arrivals = get_json(f"/StopPoint/{station_id}/Arrivals")
    # Filter arrivals
    arrivals = [
        a
        for a in arrivals
        if a.get("vehicleId")
        and a.get("expectedArrival")
        and arrival_time
        <= datetime.fromisoformat(a["expectedArrival"].replace("Z", "+00:00"))
        <= end_time
    ]
    if not arrivals:
        return []
    logger.debug("%d arrivals in window at %s", len(arrivals), station_id)
    trains = []
    # Get unique vehicles
    vehicle_ids = list(set(a["vehicleId"] for a in arrivals))
    logger.debug("%d unique vehicle ids", len(vehicle_ids))
    predictions = get_vehicle_predictions(vehicle_ids)
    # Group predictions by vehicle
    vehicles = {}
    for p in predictions:
        vehicle_id = p.get("vehicleId")
        if vehicle_id:
            vehicles.setdefault(vehicle_id, []).append(p)
    # Create train objects independently of whether vehicle predictions exist.
    for arrival in arrivals:
        if not arrival.get("destinationNaptanId"):
            logger.debug("Skipping arrival with no destinationNaptanId: %s", arrival)
            continue

        expected_str = arrival.get("expectedArrival")
        if not expected_str:
            continue
        actual_arrival_dt = datetime.fromisoformat(expected_str.replace("Z", "+00:00"))
        actual_arrival_mins = round((actual_arrival_dt - start_time).total_seconds() / 60)

        vehicle_id = arrival["vehicleId"]

        # Fetch the (cached) timetable first so we don't build a Train we then discard.
        timetable = get_timetable(
            arrival["lineId"],
            arrival["naptanId"],
            arrival["destinationNaptanId"],
        )
        if timetable is None:
            continue

        t = Train()
        t.line = arrival.get("lineName", "")
        t.direction = arrival.get("direction", "")
        t.vehicle_id = vehicle_id
        station_groups = get_station_order(timetable)

        for group in station_groups:
            stops = {}
            for name, offset in group:
                stops[name] = actual_arrival_mins + offset
            t.stops.append(stops)

        # Add live predictions for this vehicle only.
        for prediction in vehicles.get(vehicle_id, []):
            prediction_station = prediction.get("naptanId")
            if prediction_station:
                prediction_station = get_station_id(prediction_station)
            elif prediction.get("stationName"):
                try:
                    prediction_station = get_station_id(prediction["stationName"])
                except ValueError:
                    continue

            expected = prediction.get("expectedArrival")
            if prediction_station and expected:
                predicted_arrival = datetime.fromisoformat(expected.replace("Z", "+00:00"))
                predicted_minutes = round((predicted_arrival - start_time).total_seconds() / 60)
                for stops in t.stops:
                    if prediction_station in stops:
                        stops[prediction_station] = predicted_minutes

        trains.append(t)
    if logger.isEnabledFor(logging.DEBUG):
        for t in trains:
            logger.debug("Train: %s %s (%s)", t.line, t.direction, t.vehicle_id)
            for i, stops in enumerate(t.stops):
                logger.debug("  interval group %d: %s", i, stops)
    return trains


@lru_cache(maxsize=22)
def _get_routes_for_line_cached(line_id: str, direction: str) -> tuple[tuple[str, ...], ...]:
    """Cache the mostly static route sequences for each line and direction."""
    response = get_json(f"/Line/{line_id}/Route/Sequence/{direction}")
    ordered_line_routes = response.get("orderedLineRoutes", [])
    return tuple(tuple(route.get("naptanIds", [])) for route in ordered_line_routes)

def heuristic(station, end_station, station_lat_lon, heuristic_type):
    """
    Heuristic calculated assuming input is two tuples of lat and lons
    starting station (lat,lon)
    ending station (lat, lon)
    """
    if heuristic_type == "dijkstra":
        return 0
    coord1 = station_lat_lon.get(station)
    coord2 = station_lat_lon.get(end_station)
    # Find the Eueclidian distance
    dist_miles = geodesic(coord1, coord2).miles

    # Find the hueristic, distance divided by estimate max possible speed of train
    heuristic = (dist_miles / EST_MAX_TRAIN_SPEED)*60
    return heuristic


def init_route(start_station, start_time):
    """Create the initial route and populate it with departures from its start station."""
    initial_route = Route(start_station, 0)
    trains = get_trains(start_station, start_time, start_time)

    for train in trains:
        for stop_group in train.stops:
            for station_id, arrival_time in stop_group.items():
                if arrival_time <= initial_route.current_time:
                    continue

                current = initial_route.available_stations.get(station_id)
                if current is None or arrival_time < current["time"]:
                    initial_route.available_stations[station_id] = {
                        "time": arrival_time,
                        "train": train,
                    }

    return initial_route


def build_route(old_route, new_station, start_time, current_time, new_train):
    next_route = Route(new_station, current_time)
    next_route.current_trains = old_route.current_trains.copy()
    next_route.current_trains.append(new_train)
    next_route.trains = list(old_route.trains) + [new_train]
    next_route.parent = old_route
    arrival_time = start_time + timedelta(minutes=current_time)
    available_trains = get_trains(new_station, start_time, arrival_time)
    # Find available stations
    for train in available_trains:
        for group in train.stops:
            for station_id, arrival in group.items():
                if station_id == new_station:
                    continue
                if arrival > current_time:
                    if station_id not in next_route.available_stations:
                        next_route.available_stations[station_id] = {
                            "time": arrival,
                            "train": train,
                        }
    return next_route


def astar_step(
    explored_routes,
    explored_stations,
    start_time,
    end_station,
    station_lat_lon,
    heuristic_type="dijkstra",
):
    # Explored ruotes is a list of Route Objects
    # Explored_stations is string list of station names

    time_to_change = 5
    candidate_stations = {}
    for current_route in explored_routes:
        for station, details in current_route.available_stations.items():
            # Does this fetch a station name as a string, is details the arrival time?

            if station not in explored_stations:
                potential_time = details["time"]
                # Check if the train arriving at this station is different from the train we were previously on
                if current_route.parent is not None:
                    # Compare the current train to the train used in the parent route
                    previous_train = current_route.current_trains[-1] if current_route.current_trains else None
                    current_train = details["train"]
                    
                    if previous_train != current_train:
                        potential_time += time_to_change  # Only add 5 mins if it's a transfer
                if (
                    station not in candidate_stations
                    or potential_time < candidate_stations[station]["time"]
                ):
                    ## This seems to add a new available station if it is not seen
                    ## or update the station route with the new best potential time
                    ## adding the route (station information ect.) to it
                    candidate_stations[station] = {
                        "time": potential_time, # how can we know what time it will stop there, as change time is added
                        "train": details["train"],
                        "route": current_route,
                    }

    if not candidate_stations:
        logger.info("No available stations to explore. Ending search.")
        return None, None

    # for each of the shortest_routes, find the potential time to the new station, and add the heuristic value for that station. Then select the station with the lowest total time.
    potential_times = {}  # a dictionary where the key is the next station and the value is the predicted time to travel to it
    # iterate through the shortest_routes and calculate the total time for each station
    for station in candidate_stations:
        # calculate the potential time to the new station and add the heuristic value for that station
        potential_time = candidate_stations[station]["time"]
        # FIX: measure distance from the candidate station to the end station
        heuristic_value = heuristic(station, end_station, station_lat_lon, heuristic_type)
        total_time = potential_time + heuristic_value
        # add the total_time to the potential_times dictionary, with the key as potential next station
        potential_times[station] = total_time

    new_station = min(potential_times, key=potential_times.get)

    next_route = build_route(
        candidate_stations[new_station]["route"],
        new_station,
        start_time,
        candidate_stations[new_station]["time"],
        candidate_stations[new_station]["train"],

    )

    return next_route, new_station


def main(start_station, end_station, start_time):
    # Keep station identifiers consistent with the NAPTAN IDs from TfL data.
    start_station = get_station_id(start_station)
    end_station = get_station_id(end_station)

    initial_route = init_route(start_station, start_time)
    if not initial_route.available_stations:
        return None

    # Get station lat and lon in dictionary {NapTan: (lat,lon)}
    station_lat_lon = get_stations_lon_lat_dictionary()

    route_found = False
    explored_routes = [initial_route]
    explored_stations = [start_station]
    while not route_found:
        next_route, next_station = astar_step(
            explored_routes, explored_stations, start_time, end_station, station_lat_lon, heuristic_type="euclidean"
        )
        if next_route is None:
            return None

        if next_station == end_station:
            next_route.route_complete = True
            return next_route

        explored_routes.append(next_route)
        explored_stations.append(next_station)
        if next_route.route_complete:
            logger.debug("Route complete: %s", route_stations(next_route))
            route_found = True


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")  # DEBUG for detail
    start_time = datetime.now(timezone.utc)
    for start, end in [
        # ("Baker Street", "Bank"),
        # ("King's Cross St. Pancras", "Waterloo"),
        # ("Stratford", "Victoria"),
        # ("Canary Wharf", "Liverpool Street"),
        ("Oxford Circus", "Wimbledon"),
    ]:
        route = main(start, end, start_time)
        if route is None:
            print(f"No route found from {start} to {end}.")
        else:
            print(format_route(route, start_time))