import requests
import json
from datetime import timedelta, datetime, timezone
from functools import lru_cache
from dataclasses import dataclass

BASE_URL = "https://api.tfl.gov.uk"

"""Opening the NAPTAN json to avoid constantly reopening it"""
with open("naptan.json") as f:
    NAPTAN = json.load(f)

STATION_NAMES = {
    s["naptanID"]: s["commonName"]
    for s in NAPTAN
}
STATION_IDS = {
    s["commonName"].casefold(): s["naptanID"]
    for s in NAPTAN
}
class train: #represents the physical train and the stops that it takes
    def __init__(self):
        self.line = "" #line that the train is on
        self.direction = "" #inbound/outbound train
        self.stops = [] #list of dictionaries, with station names and relative times. Each one represents a variation on that route that the train could take

class station:#possibly defunct
    def __init__(self):
        self.coordinates


class route: #represnts one stop on journey. linked to previous stops.
    def __init__(self, station, arrival_time):
        self.station = station #the station (node) that route represents
        self.current_time = arrival_time #this eventually holds the current time in datetime format - if route is not the first station, is updated by new route function
        self.current_trains = [] #trains used to get to this station
        self.available_stations = {} #available stations and their times from get_trains
        self.parent = None #if route is not first station, links to previous route object
        self.total_time = 0 #time in minutes since journey started
        self.route_complete = False #checks if route has been completed. If this os true, this is the final route object in the chain.


def get_json(path):
    """
    Fetch BASE_URL + path and return the JSON response.
    Raise requests.exceptions.RequestException for any request errors.
    """
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

def get_station_id(station):#gets the station from the stationname string
    # Allow NAPTAN IDs directly
    if station.upper().startswith("9"):
        return station.upper()
    if station.endswith(" Underground Station"):
        return station
    # Use the station lookup loaded at startup instead of rereading the file.
    station_id = STATION_IDS.get((station+ " Underground Station").casefold()) #changes the format to get stations from the json
    if station_id:
        return station_id
    raise ValueError(f"Station not found: {station}")

def get_vehicle_predictions(vehicle_ids): #some trains have vehicle ids that track their jouneys(not all). this function gets the timetable for those trains
    predictions = []
    for i in range(0, len(vehicle_ids), 25):
        ids = ",".join(vehicle_ids[i:i+25])
        data = get_json(f"/Vehicle/{ids}/Arrivals")
        predictions.extend(data)
    return predictions

def calculate_times(start_time, scheduled, live): #combines live predictions and timetables
    result = {}
    for station, scheduled_time in scheduled.items():
        if station in live:
            arrival = live[station]
        else:
            arrival = scheduled_time
            result[station] = round((arrival - start_time).total_seconds() / 60)
    return result

def get_station_order(timetable):
    route = timetable["timetable"]["routes"][0]
    station_groups = []
    for interval_group in route["stationIntervals"]:
        stations = []
        for interval in interval_group["intervals"]:
            station_id = interval["stopId"]
            name = STATION_NAMES.get(station_id)
            if name:
                stations.append((
                    name,
                    interval["timeToArrival"]
                ))
        station_groups.append(stations)
    return station_groups

def get_trains(station, start_time, arrival_time,minutes=30): #this function collects the trains from a given station
    #gets the station id from input
    station_id = get_station_id(station)
    #calculates the timedate formatted end time
    end_time = arrival_time + timedelta(minutes=minutes)
    #gets a list of all the arrivals to the given station
    arrivals = get_json(f"/StopPoint/{station_id}/Arrivals")
    # Filter arrivals for time they arrive and make sure they are in the time window
    arrivals = [
        a for a in arrivals
        if a.get("vehicleId")
        and a.get("expectedArrival")
        and arrival_time <= datetime.fromisoformat(
            a["expectedArrival"].replace("Z", "+00:00")
        ) <= end_time]
    trains = []
    # Get unique vehicles
    vehicle_ids = list(set(
        a["vehicleId"] for a in arrivals))
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
        t = train()
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
                f"/Line/{timetable_key[0]}/Timetable/"
                f"{timetable_key[1]}/to/{timetable_key[2]}")
        timetable = timetables[timetable_key]
        #gets the station order for a given line
        station_groups = get_station_order(timetable)
        #for the order, fills in the time with the minutes
        for group in station_groups:
            stops = {}
            for name, minutes in group:
                stops[name] = round((arrival_time - start_time).total_seconds() / 60 + minutes)
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


def heuristic(last_station,new_station,heuristic_type = "djistraka"): #ADD ACTUAL HEURISTIC HERE
    if (heuristic_type== "djistraka"):
        return 0
    else:
        return 0

def init_route(start_station):
    new_route = route(start_station, 0)
    return new_route

def new_route(old_route,new_station,start_time,current_time,new_train):
    new_route = route(new_station,current_time)
    new_route.current_trains = old_route.current_trains.copy()
    new_route.current_trains.append(new_train)
    new_route.parent = old_route
    arrival_time = start_time + timedelta(minutes=current_time)
    available_trains = get_trains(
        new_station,
        start_time,
        arrival_time)
    # Find available stations
    for train in available_trains:
        for group in train.stops:
            for station, arrival in group.items():
                if arrival > current_time:
                    if station not in new_route.available_stations:
                        new_route.available_stations[station] = {
                            "time": arrival,
                            "train": train }
                    elif arrival < new_route.available_stations[station]["time"]:
                        new_route.available_stations[station] = {
                            "time": arrival,
                            "train": train }
    return new_route


def astar_step(explored_routes, explored_stations, heuristic = "djistraka"): #it is misspelled. fix later
    time_to_change = 5
    available_stations = {} #check that dicts are ordered
    for route in explored_routes:
        for station, details in route.available_stations.items():
            if station not in explored_stations:
                potential_time = details["time"]
                if route.parent is not None:
                    potential_time += time_to_change
                if (station not in available_stations or potential_time < available_stations[station]["time"]):
                    available_stations[station] = {
                        "time": potential_time,
                        "train": details["train"],
                        "route": route }
    shortest_routes = []
    current_shortest = float("inf")
    for x in available_stations:
        if available_stations[x]["time"] < current_shortest:
            shortest_routes = [x]
            current_shortest = x["time"]
        if available_stations[x]["time"] == current_shortest:
            shortest_routes.append(x)
    for x in shortest_routes:
        pass
        #find the shortest time via available_station
    #make new route which is the route from shortest_routes that has the shortest time plus the new station with route object updated accordingly
    return new_route, new_station




def main(start_station,end_station,start_time):
    route_found = False
    routes = [init_routes(start_station)]
    explored_stations = [start_station]
    while route_found == False:
        new_route, new_station = astar_step(routes,explored_stations)
        routes.append(new_route)
        explored_stations.append(new_station)
        #if new_route.completion_status = True:
        #    print(new_route)
        #    route_found == True




print(get_trains("Waterloo",datetime.now(timezone.utc),datetime.now(timezone.utc)))
#if __name__ == "__main__":
    #main()
