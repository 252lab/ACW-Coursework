import json
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from geopy.distance import geodesic
import requests

BASE_URL = "https://api.tfl.gov.uk"

"""Opening the NAPTAN json to avoid constantly reopening it"""
with (Path(__file__).with_name("naptan.json")).open(encoding="utf-8") as f:
    NAPTAN = json.load(f)

STATION_NAMES = {s["naptanID"]: s["commonName"] for s in NAPTAN}
STATION_IDS = {s["commonName"].casefold(): s["naptanID"] for s in NAPTAN}
EST_MAX_TRAIN_SPEED = 60 # tfl says that trains can reach about 60 mph

class Train:
    def __init__(self):
        self.line = ""
        self.direction = ""
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


def get_json(path):
    """
    Fetch BASE_URL + path and return the JSON response.
    Raise requests.exceptions.RequestException for any request errors.
    """
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

""" Fetches the stations long and lats from a csv file
    Converts fetched values from file and returns
    a dictionary of station NapTans and their lons and lats
    {String: (float,float)}
    """
def get_stations_lon_lat_dictionary(station_coord_csv=r"../tfl-stationdata-detailed/StationPoints.csv"):
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
    # Allow NAPTAN IDs directly
    if station.upper().startswith("9"):
        return station.upper()
    # Accept a full common name ("Oxford Circus Underground Station") or a short one ("Oxford Circus").
    # Add " Underground Station" if a short name is provided.
    for name in (station, station + " Underground Station"):
        station_id = STATION_IDS.get(name.casefold())
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
            name = STATION_NAMES.get(station_id)
            if name:
                stations.append((name, interval["timeToArrival"]))
        station_groups.append(stations)
    return station_groups


def get_trains(station, start_time, arrival_time, minutes=30):
    station_id = get_station_id(station)
    print("station id is " + station_id)
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
    print("there are " + str(len(arrivals)) + " arrivals")
    trains = []
    # Get unique vehicles
    vehicle_ids = list(set(a["vehicleId"] for a in arrivals))
    print("there are " + str(len(vehicle_ids)) + " vehicle ids")
    predictions = get_vehicle_predictions(vehicle_ids)
    # Group predictions by vehicle
    vehicles = {}
    for p in predictions:
        vehicle_id = p.get("vehicleId")
        if vehicle_id:
            vehicles.setdefault(vehicle_id, []).append(p)
    # Create train objects
    timetables = {}
    for arrival in arrivals:
        if not arrival.get("destinationNaptanId"):
            print("Missing destinationNaptanId: ")
            print(arrival)
            continue
        vehicle_id = arrival["vehicleId"]
        t = Train()
        t.line = arrival.get("lineName", "")
        t.direction = arrival.get("direction", "")
        # Reuse timetable data when multiple arrivals share the same trip.
        timetable_key = (
            arrival["lineId"],
            arrival["naptanId"],
            arrival["destinationNaptanId"],
        )
        if timetable_key not in timetables:
            timetables[timetable_key] = get_json(
                f"/Line/{timetable_key[0]}/Timetable/" f"{timetable_key[1]}/to/{timetable_key[2]}"
            )
        timetable = timetables[timetable_key]
        station_groups = get_station_order(timetable)
        for group in station_groups:
            stops = {}
            for name, offset in group:
                stops[name] = round((arrival_time - start_time).total_seconds() / 60 + offset)
            t.stops.append(stops)
        # Add live predictions for this vehicle only
        for p in vehicles.get(vehicle_id, []):
            name = p.get("stationName")
            expected = p.get("expectedArrival")
            if name and expected:
                predicted_arrival = datetime.fromisoformat(expected.replace("Z", "+00:00"))
                predicted_minutes = round((predicted_arrival - start_time).total_seconds() / 60)
                for stops in t.stops:
                    if name in stops:
                        stops[name] = predicted_minutes
        trains.append(t)
    for t in trains:
        print("\nLine:", t.line)
        print("Direction:", t.direction)

        for i, stops in enumerate(t.stops):
            print(f"Interval group {i}:")
            print(stops)
    return trains


@lru_cache(maxsize=22)
def _get_routes_for_line_cached(line_id: str, direction: str) -> tuple[tuple[str, ...], ...]:
    """Cache the mostly static route sequences for each line and direction."""
    response = get_json(f"/Line/{line_id}/Route/Sequence/{direction}")
    ordered_line_routes = response.get("orderedLineRoutes", [])
    return tuple(tuple(route.get("naptanIds", [])) for route in ordered_line_routes)

""" Hueristic calculated assuming input is two tuples of lat and lons
    starting station (lat,lon)
    ending station (lat, lon)
    """
def heuristic(last_station, new_station, heuristic_type="dijkstra"):  # ADD ACTUAL HEURISTIC HERE
    if heuristic_type == "dijkstra":
        return 0
    else:
        # Find the Eueclidian distance
        dist_miles = geodesic(last_station, new_station).miles

        # Find the hueristic, distance divided by estimate max possible speed of train
        hueristic = dist_miles / EST_MAX_TRAIN_SPEED
        return hueristic


def init_route(start_station, start_time):
    """Create the initial route and populate it with departures from its start station."""
    initial_route = Route(start_station, 0)
    trains = get_trains(start_station, start_time, start_time)

    for train in trains:
        for stop_group in train.stops:
            for station_name, arrival_time in stop_group.items():
                if arrival_time <= initial_route.current_time:
                    continue

                current = initial_route.available_stations.get(station_name)
                if current is None or arrival_time < current["time"]:
                    initial_route.available_stations[station_name] = {
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
            for station_name, arrival in group.items():
                if station_name == new_station:
                    continue
                if arrival > current_time:
                    if station_name not in next_route.available_stations:
                        next_route.available_stations[station_name] = {
                            "time": arrival,
                            "train": train,
                        }
    return next_route


def astar_step(explored_routes, explored_stations, start_time, heuristic_type="dijkstra"):
    time_to_change = 5
    available_stations = {} 
    for current_route in explored_routes:
        for station, details in current_route.available_stations.items():
            if station not in explored_stations:
                potential_time = details["time"]
                if current_route.parent is not None:
                    potential_time += time_to_change
                if (
                    station not in available_stations
                    or potential_time < available_stations[station]["time"]
                ):
                    available_stations[station] = {
                        "time": potential_time,
                        "train": details["train"],
                        "route": current_route,
                    }

    if not available_stations: # NEW: return None, None if there are no available stations to explore
        print("No available stations to explore. Ending search.")
        return None, None

    shortest_routes = []
    current_shortest = float("inf")
    for x in available_stations:
        if available_stations[x]["time"] < current_shortest:
            shortest_routes = [x]
            current_shortest = available_stations[x]["time"] # FIX: changed to available_stations[x]["time"] to get the correct time for the station
        elif available_stations[x]["time"] == current_shortest:
            shortest_routes.append(x)

    # for each of the shortest_routes, find the potential time to the new station, and add the heuristic value for that station. Then select the station with the lowest total time.
    for x in shortest_routes:
        potential_times = (
            {}
        )  # a dictionary where the key is the next station and the value is the predicted time to travel to it
        # iterate through the shortest_routes and calculate the total time for each station
        for station in shortest_routes:
            # calculate the potential time to the new station and add the heuristic value for that station
            potential_time = available_stations[station]["time"]
            # calculate the heuristic value to the new station
            heuristic_value = heuristic(
                available_stations[station]["route"].station, station, heuristic_type
            )
            # calculate the total time from the current station to the next station, using the potential time and the heuristic value
            total_time = potential_time + heuristic_value
            # add the total_time to the potential_times dictionary, with the key as potential next station
            potential_times[station] = total_time

        # make a new route which is the route from shortest_routes that has the shortest time plus the new station
        for (
            time
        ) in (
            potential_times
        ):  # iteratre through the potential_times dictionary and find the station with the shortest time
            if potential_times[time] == min(
                potential_times.values()
            ):  # if the time is the shortest time, then make a new route with that station and return it
                new_station = time  # set the new station to the station with the shortest time
                next_route = build_route(
                    available_stations[new_station]["route"],
                    new_station,
                    start_time,
                    available_stations[new_station]["time"],
                    available_stations[new_station]["train"],
                )  # make a new route with the shortest time and the new station
                break

    return next_route, new_station


def main(start_station, end_station, start_time):
    initial_route = init_route(start_station, start_time)
    if not initial_route.available_stations:
        return None

    route_found = False
    routes = [initial_route]
    explored_stations = [start_station]
    while not route_found:
        next_route, next_station = astar_step(routes, explored_stations, start_time)
        if next_route is None:
            return None

        if next_station == end_station:
            next_route.route_complete = True
            return next_route

        routes.append(next_route)
        explored_stations.append(next_station)
        if next_route.route_complete:
            print(next_route)
            route_found = True


if __name__ == "__main__":
    for start, end in [
        ("Baker Street", "Bank"),
        ("Oxford Circus", "King’s Cross St. Pancras"),
        ("Oxford Circus", "Bond Street"),
    ]:
        route = main(start, end, datetime(2026, 11, 17, 11, 0, tzinfo=timezone.utc))
        if route is None:
            print(f"No route found from {start} to {end}.")
        else:
            print(f"Route from {start} to {end}: {route_stations(route)}")

