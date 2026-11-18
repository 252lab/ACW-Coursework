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
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup
import secrets


app = Flask(__name__,template_folder="templates")

# generating secret key
secret_key = secrets.token_hex(16)
app.config['SECRET_KEY'] = secret_key


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

# Cache live arrivals with TTL so we don't spam TfL or timeout
ARRIVAL_CACHE = {}
ARRIVAL_CACHE_TTL_SECONDS = 30  

class Train:
    def __init__(self):
        self.line = ""
        self.direction = ""
        self.vehicle_id = ""
        self.stops = []

class Route:
    def __init__(self, station, current_time, arrival_time=None):
        self.station = station
        self.current_time = current_time  # When we are ready / departing
        self.arrival_time = arrival_time if arrival_time is not None else current_time

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


def format_route(route, start_time):
    """Return a readable, leg-by-leg description of a completed route, with correct times and wait durations."""
    stations = route_stations(route)
    
    nodes = []
    current = route
    while current is not None:
        nodes.append(current)
        current = current.parent
    nodes = list(reversed(nodes))

    def clock(minutes):
        return (start_time + timedelta(minutes=minutes)).astimezone().strftime("%H:%M")

    legs = []
    for i, train in enumerate(route.trains):
        from_node = nodes[i]
        to_node = nodes[i + 1]

        arrive_time = getattr(to_node, "arrival_time", to_node.current_time)

        if legs and legs[-1]["vehicle_id"] == train.vehicle_id:
            legs[-1]["to"] = stations[i + 1]
            legs[-1]["arrive"] = arrive_time
        else:
            depart_time = from_node.current_time if i > 0 else from_node.arrival_time
            legs.append({
                "line": train.line,
                "vehicle_id": train.vehicle_id,
                "from": stations[i],
                "to": stations[i + 1],
                "depart": depart_time,
                "arrive": arrive_time,
            })

    lines = [
        f"{station_label(stations[0])} → {station_label(stations[-1])}"
        f"  (about {route.current_time} min, arriving {clock(route.current_time)})",
        "",
    ]
    for n, leg in enumerate(legs, start=1):
        if n > 1:
            prev_leg = legs[n - 2]
            transfer_wait = leg["depart"] - prev_leg["arrive"]
            
            # Force the transfer wait to look at least like a valid 5 min transfer if the data collapsed it to 0
            if transfer_wait <= 0:
                transfer_wait = 5
                leg["depart"] = prev_leg["arrive"] + transfer_wait
                
            lines.append(f"   Change at {station_label(leg['from'])} (wait {transfer_wait} min)")
        lines.append(
            f"{n}. {leg['line']} line: "
            f"{clock(leg['depart'])} {station_label(leg['from'])} → "
            f"{clock(leg['arrive'])} {station_label(leg['to'])}"
        )
    return "\n".join(lines)


def get_json(path):
    params = {"app_key": APP_KEY} if APP_KEY else None
    response = SESSION.get(f"{BASE_URL}{path}", params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def get_cached_arrivals(station_id):
    """Fetches live arrivals with TTL cache so we don't spam TfL or timeout"""
    now = datetime.now(timezone.utc)
    if station_id in ARRIVAL_CACHE:
        cached_time, arrivals_data = ARRIVAL_CACHE[station_id]
        if (now - cached_time).total_seconds() < ARRIVAL_CACHE_TTL_SECONDS:
            return arrivals_data

    arrivals_data = get_json(f"/StopPoint/{station_id}/Arrivals")
    ARRIVAL_CACHE[station_id] = (now, arrivals_data)
    return arrivals_data


def get_stations_lon_lat_dictionary(
    station_coord_csv=Path(__file__).resolve().parent.parent
    / "tfl-stationdata-detailed"
    / "StationPoints.csv",
):
    if not station_coord_csv.exists():
        return {}
    points = pd.read_csv(station_coord_csv)
    tube_points = points[points["StationUniqueId"].str.startswith("940GZZLU", na=False)]
    unique_points = tube_points.drop_duplicates(subset=["StationUniqueId"])

    coord_dict = {}
    for _, row in unique_points.iterrows():
        naptan = row["StationUniqueId"]
        lat = row["Lat"]
        lon = row["Lon"]
        coord_dict[naptan] = (lat, lon)

    return coord_dict


def get_station_id(station):
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


def get_vehicle_predictions(vehicle_ids):
    predictions = []
    for i in range(0, len(vehicle_ids), 25):
        ids = ",".join(vehicle_ids[i : i + 25])
        try:
            data = get_json(f"/Vehicle/{ids}/Arrivals")
            predictions.extend(data)
        except Exception:
            pass
    return predictions


def calculate_times(start_time, scheduled, live):
    result = {}
    for station, scheduled_time in scheduled.items():
        arrival = live.get(station, scheduled_time)
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
    try:
        return get_json(f"/Line/{line_id}/Timetable/{from_id}/to/{to_id}")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            raise
        return None


def get_trains(station, start_time, arrival_time, minutes=30):
    station_id = get_station_id(station)
    logger.debug("Fetching arrivals for %s", station_id)
    end_time = arrival_time + timedelta(minutes=minutes)
    
    try:
        arrivals = get_cached_arrivals(station_id)
    except Exception:
        return []

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
    
    trains = []
    vehicle_ids = list(set(a["vehicleId"] for a in arrivals))
    predictions = get_vehicle_predictions(vehicle_ids)
    
    vehicles = {}
    for p in predictions:
        vehicle_id = p.get("vehicleId")
        if vehicle_id:
            vehicles.setdefault(vehicle_id, []).append(p)

    for arrival in arrivals:
        if not arrival.get("destinationNaptanId"):
            continue

        expected_str = arrival.get("expectedArrival")
        if not expected_str:
            continue
        actual_arrival_dt = datetime.fromisoformat(expected_str.replace("Z", "+00:00"))
        actual_arrival_mins = round((actual_arrival_dt - start_time).total_seconds() / 60)

        vehicle_id = arrival["vehicleId"]

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
        
        try:
            station_groups = get_station_order(timetable)
        except (KeyError, IndexError):
            continue

        for group in station_groups:
            stops = {}
            for name, offset in group:
                stops[name] = actual_arrival_mins + offset
            t.stops.append(stops)

        for prediction in vehicles.get(vehicle_id, []):
            prediction_station = prediction.get("naptanId")
            if prediction_station:
                try:
                    prediction_station = get_station_id(prediction_station)
                except ValueError:
                    continue
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
    return trains


@lru_cache(maxsize=22)
def _get_routes_for_line_cached(line_id: str, direction: str) -> tuple[tuple[str, ...], ...]:
    response = get_json(f"/Line/{line_id}/Route/Sequence/{direction}")
    ordered_line_routes = response.get("orderedLineRoutes", [])
    return tuple(tuple(route.get("naptanIds", [])) for route in ordered_line_routes)


def heuristic(station, end_station, station_lat_lon, heuristic_type):
    if heuristic_type == "dijkstra" or not station_lat_lon:
        return 0
    coord1 = station_lat_lon.get(station)
    coord2 = station_lat_lon.get(end_station)
    
    if not coord1 or not coord2:
        return 0

    dist_miles = geodesic(coord1, coord2).miles
    heuristic_val = (dist_miles / EST_MAX_TRAIN_SPEED) * 60
    return heuristic_val


def init_route(start_station, start_time):
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


def build_route(old_route, new_station, start_time, arrival_time, ready_time, new_train):
    next_route = Route(new_station, ready_time, arrival_time=arrival_time)
    next_route.current_trains = old_route.current_trains.copy()
    next_route.current_trains.append(new_train)
    next_route.trains = list(old_route.trains) + [new_train]
    next_route.parent = old_route
    
    search_time = start_time + timedelta(minutes=ready_time)
    available_trains = get_trains(new_station, start_time, search_time)
    
    for train in available_trains:
        for group in train.stops:
            for station_id, arrival in group.items():
                if station_id == new_station:
                    continue
                if arrival > ready_time:
                    current = next_route.available_stations.get(station_id)
                    if current is None or arrival < current["time"]:
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
    time_to_change = 5
    candidate_stations = {}
    for current_route in explored_routes:
        for station, details in current_route.available_stations.items():
            if station not in explored_stations:
                train_arrival_time = details["time"]
                effective_ready_time = train_arrival_time

                # Only add transfer penalty if we are switching between two different trains mid-journey
                if current_route.current_trains:
                    previous_train = current_route.current_trains[-1]
                    current_train = details["train"]
                    
                    if previous_train.vehicle_id != current_train.vehicle_id:
                        effective_ready_time += time_to_change

                if (
                    station not in candidate_stations
                    or effective_ready_time < candidate_stations[station]["ready_time"]
                ):
                    candidate_stations[station] = {
                        "time": train_arrival_time,
                        "ready_time": effective_ready_time,
                        "train": details["train"],
                        "route": current_route,
                    }

    if not candidate_stations:
        logger.info("No available stations to explore. Ending search.")
        return None, None

    potential_times = {}
    for station in candidate_stations:
        potential_time = candidate_stations[station]["ready_time"]
        heuristic_value = heuristic(station, end_station, station_lat_lon, heuristic_type)
        total_time = potential_time + heuristic_value
        potential_times[station] = total_time

    new_station = min(potential_times, key=potential_times.get)

    next_route = build_route(
        candidate_stations[new_station]["route"],
        new_station,
        start_time,
        candidate_stations[new_station]["time"],
        candidate_stations[new_station]["ready_time"],
        candidate_stations[new_station]["train"],
    )

    return next_route, new_station


def main(start_station, end_station, start_time):
    start_station = get_station_id(start_station)
    end_station = get_station_id(end_station)

    initial_route = init_route(start_station, start_time)
    if not initial_route.available_stations:
        return None

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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    start_time = datetime.now(timezone.utc)
    for start, end in [
        ("Stratford", "Victoria"),
    ]:
        print(f"\nFinding route from {start} to {end}...")
        route = main(start, end, start_time)
        if route is None:
            print(f"No route found from {start} to {end}.")
        else:
            print("\n" + format_route(route, start_time))


# rendering the starting page
@app.route("/")
def index_page():
    return render_template("index.html")

# rendering the route page
@app.route("/route")
def route_page():
    return render_template("route.html")

#switching to index page
def to_index():
    return redirect(url_for('index_page'))

# switching to route page
def to_route():
    return redirect(url_for('route_page'))


""" 
This subroutine is used to retrieve the form inputs from the index.html page, and verify that they are valid.
If they inputs are not valid, an error message will be displayed and the user will be promted to re-enter their
inputs. If the inputs are valid, they will then be sent to the algorithm.
"""
@app.route("/route_input", methods=["POST"])
def route_input():

    # initialising input variables
    startLocation = ""
    endLocation = ""
    startTime = ""

    # if the form request method is post
    if request.method=="POST":

        # try to get the form inputs
        # removing any extra spaces and changing them to lowecase, to make it 
        # easier to verify
        try:
            startLocation = request.form.get("startLocation","").strip()
            endLocation = request.form.get("endLocation","").strip()

            # default is an empty string if no input for the time
            startTime = request.form.get("startTime", "").strip()

            # call function to validate inputs (and update then when necessary)
            startLocation, endLocation, startTime = validate_inputs(startLocation, endLocation, startTime)

            #TODO - BACKEND STARTS HERE!!!!

            return show_route()

        except:
             message = "Form elements cannot be retrieved."
             return error_found(message)
                    
        return to_route()



# function used to check if stations can be matched to API
# also checks that the user has only entered one of the start and end time
def validate_inputs(startLocation, endLocation, startTime):

    # assigning variables
    startID = ""
    endID = ""
    
    #validating station names
    try:
        # check if start station and end station can be found in the API/data
        if (startLocation.strip().lower() == endLocation.strip().lower()):

            # output an error message about this
            message = "Please enter two different stations."
            return error_found(message)

        else:

            # otherwise try and find station data
            startID = find_station(startLocation)
            endID = find_station(endLocation)

            #if either id is -1, it cannot be found
            if (startID == -1 or endID == -1):

                # output the error message
                message = "One or both of your stations could not be found."
                return error_found(message)

    except:
        # if exception is raised, assume something is wrong with inputs
        message = "Couldn't validate station inputs."
        return error_found(message)
    
    # validating time inputs
    try:
        # if no time is entered, get the current time as the start time
        if (startTime == ""):
            startTime = datetime.datetime.now()
            
    except:
        # outputting error
        message = "Couldn't validate time inputs."
        return error_found(message)

    # if all the inputs thaty have been entered are valid

    # returning the validated inputs
    return startID, endID, startTime


#checking if the station is valid
# return station ID if found
def find_station(stationName):

    # converting the station name to lower case and removing any extra paces
    toMatch = stationName.lower().replace(" ", "")
    found = False


    # searching the array of stations fopr a match
    try:

        # getting array of stations
        listStations = sorted(list_stations())

        # searching the array of stations for a match
        start = 0
        end = len(listStations) -1

        while start <= end:
            mid = (start+end) // 2
            midpoint = listStations[mid][0]

            if midpoint > toMatch:
                end = mid -1

            elif midpoint < toMatch:
                start = mid + 1
            else:
                #return the Id of the station
                return listStations[mid][1]

        # return -1 if the station could not be found
        return -1
    
    except:
        message = "Something went wrong."
        error_found(message)

# returning the list of stations
def list_stations():
    
    # filepath for csv file
    filepath = "tfl-stationdata-detailed/Stations.csv"

    try:

        # reading from the csv file
        df = pd.read_csv(filepath)

        # getting the tube stations
        tube_stations = df[df["UniqueId"].str.startswith("940GZZLU", na=False)]

        # converting to an array
        # data should already be ordered as it is in the csv file
        tube_names = tube_stations[["Name", "UniqueId"]].to_numpy()

        # making the staion names lowercase and removing any spaces
        # for easier searching
        for i in range(0, len(tube_names)):
            tube_names[i][0]= tube_names[i][0].lower().replace(" ", "")

        print(len(tube_names))
        # returning list of stations
        return tube_names

    except:
        message = "Couldn't retrive list of stations in network."
        error_found(message)


# outputs the error message
# and returns to the index page
def error_found(message):
    flash(message, 'error')
    return to_index()

# displaying the outputted route
def show_route(text):

    # initial route string
    route_output = "<br><p style='text-align: center; font-family: Arial, Helvetica, sans-serif;' >" + text + "</p><br>"

    try:

        # switching to the route page
        return render_template("route.html", injected_html=Markup(route_output))

    # catches anything that goes wrong
    except:
        message = "Something went wrong."
        error_found(message)
    

if __name__ == "__main__":
    app.run(debug=True)

