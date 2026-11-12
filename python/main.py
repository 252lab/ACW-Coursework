import requests
import json
from datetime import timedelta, datetime, timezone
from functools import lru_cache

BASE_URL = "https://api.tfl.gov.uk"

"""Opening the NAPTAN json to avoid constantly reopening it"""
with open("python/naptan.json") as f:
    NAPTAN = json.load(f)

STATION_NAMES = {
    s["naptanID"]: s["commonName"]
    for s in NAPTAN
}
STATION_IDS = {
    s["commonName"].casefold(): s["naptanID"]
    for s in NAPTAN
}
class train:
    def __init__(self):
        self.line = ""
        self.direction = ""
        self.stops = {}

class station:
    def __init__(self):
        self.trains = []


class route:
    current_platforms = [] #list of platform objects
    available_platforms = {} #combination of all of the station_left_on_route dictionaries from current_platform objects
                             #plus other platforms in the available stations
    current_time = 0


def get_json(path):
    """
    Fetch BASE_URL + path and return the JSON response.
    Raise requests.exceptions.RequestException for any request errors.
    """
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

def get_station_id(station):
    # Allow NAPTAN IDs directly
    if station.upper().startswith("9"):
        return station.upper()

    # Use the station lookup loaded at startup instead of rereading the file.
    station_id = STATION_IDS.get(station.casefold())
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
    stations = []
    for interval_group in route["stationIntervals"]:
        for interval in interval_group["intervals"]:
            station_id = interval["stopId"]
            name = STATION_NAMES.get(station_id)
            if name:
                stations.append((name, interval["timeToArrival"]))
    return stations

def get_trains(station, start_time, origin_time,minutes=30):
    station_id = get_station_id(station)
    print("station id is "+ station_id)
    end_time = start_time + timedelta(minutes=minutes)
    arrivals = get_json(f"/StopPoint/{station_id}/Arrivals")
    # Filter arrivals
    arrivals = [
        a for a in arrivals
        if a.get("vehicleId")
        and a.get("expectedArrival")
        and start_time <= datetime.fromisoformat(
            a["expectedArrival"].replace("Z", "+00:00")
        ) <= end_time]
    print("there are "+str(len(arrivals))+" arrivals")
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
                f"{timetable_key[1]}/to/{timetable_key[2]}"
            )
        timetable = timetables[timetable_key]
        station_order = get_station_order(timetable)
        for name, minutes in station_order:
            t.stops[name] = round((origin_time - start_time).total_seconds() / 60 + minutes
            )
        print("Station order:", station_order)
        print("Number of stations:", len(station_order))
        # Initialise stops in timetable order
        for name in station_order:
            t.stops[name] = None
        # Add live predictions for this vehicle only
        for p in vehicles.get(vehicle_id, []):
            name = p.get("stationName")
            expected = p.get("expectedArrival")
            if name in t.stops and expected:
                arrival_time = datetime.fromisoformat(
                    expected.replace("Z", "+00:00"))
                t.stops[name] = round(
                    (arrival_time - start_time).total_seconds() / 60)
        trains.append(t)
    return trains

def get_tube_routes():
    """
    Fetch all tube routes from the TFL API.
    Returns a list of tube route dictionaries.
    """
    return get_json("/Line/Mode/tube")


def get_stop_point(stop_point_id):
    """
    Fetch a specific stop point from the TFL API.
    Returns a dictionary containing the stop point details.
    """
    return get_json(f"/StopPoint/{stop_point_id}")


def access_stop_point(stop_point_id):
    """
    Access a specific stop point and return its keys.
    """
    try:
        stop = get_stop_point(stop_point_id)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stop point: {e}")
        return
    return set(stop.keys())


@lru_cache(maxsize=22)
def _get_routes_for_line_cached(line_id: str, direction: str) -> tuple[tuple[str, ...], ...]:
    """Cache the mostly static route sequences for each line and direction."""
    response = get_json(f"/Line/{line_id}/Route/Sequence/{direction}")
    ordered_line_routes = response.get("orderedLineRoutes", [])
    return tuple(tuple(route.get("naptanIds", [])) for route in ordered_line_routes)


def get_routes_for_line(line_id: str, direction: str) -> list[list[str]]:
    """
    Fetch all routes for a specific line from the TFL API.
    Returns a list of naptanIds for each route in the specified direction (inbound or outbound).
    """
    return [list(route) for route in _get_routes_for_line_cached(line_id, direction)]


def get_routes_between_two_stops_from_api(start, destination):
    """
    Fetch all tube routes from the TFL API and filter them to find routes that connect the start and destination stops.
    Return a dictionary of relevant routes with their stop sequences.
    NOTE: This only works for max. one switch between lines. If the route requires more than one switch, it will not be found.
    TODO: Rewrite this function to include a more robust pathfinding algorithm that can handle multiple line switches and find the optimal route.
    NOTE: This function is currently not used in the codebase, but it could be edited to be used in the future for finding routes between two stops.
    """

    all_routes = get_tube_routes()  # Fetch all tube routes from the TFL API
    relevant_routes = {}

    for route in all_routes:
        route_id = route.get("id")
        if not route_id:
            continue

        try:
            route_sequence = get_json(f"/Line/{route_id}/Route/Sequence")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching stop points for route {route_id}: {e}")
            continue

        if start in route_sequence and destination in route_sequence:
            relevant_routes[route_id] = route_sequence

    return relevant_routes


def get_list_of_lines():
    """
    Creates a list of one-value dictionaries.
    The line is the key, and the value is a list of dictionaries containing the inbound and outbound stop lists.
    """
    # list of valid tube lines
    LINES = [
        "bakerloo",
        "central",
        "circle",
        "district",
        "hammersmith-city",
        "jubilee",
        "metropolitan",
        "northern",
        "piccadilly",
        "victoria",
        "waterloo-city",
    ]
    stop_list = []
    for line in LINES:
        line_list = {line: []}
        for direction in ["inbound", "outbound"]:  # get the inbound/outbound list as separate
            routes = get_routes_for_line(line, direction)
            naptan_ids = routes[0]
            direction_stop_list = {direction: naptan_ids}
            line_list[line].append(direction_stop_list)
        stop_list.append(line_list)
    return stop_list


def get_list_of_stops(routes):
    """
    Returns an ordered list of stops from the routes.
    """
    stops = []
    for route in routes:
        for stop in route:
            if stop not in stops:
                stops.append(stop)
    return sorted(stops)


def construct_graph(routes, stops=None):
    """
    Construct a dictionary-based graph from a list of routes.
    Each stop is a key, and its value is a list of stops it connects to.
    Not allowing bidirectional travel.
    """
    if stops is None:
        stops = get_list_of_stops(routes)

    graph = {stop: [] for stop in stops}
    for route in routes:
        for i in range(len(route) - 1):
            graph.setdefault(route[i], []).append(route[i + 1])

    for stop in graph:
        graph[stop] = list(sorted(set(graph[stop])))
    return graph

def find_time(node, start_node, node_distances, graph):
    """
    Function to find the time to reach a node from the start node, based on the current node distances and the graph structure.
    """
    pass

def find_route(graph, start, destination):
    """
    Find a route from start to destination using the A* algorithm.
    This function should return a list of nodes representing the path from start to destination.
    (currently a placeholder for the actual implementation)
    """
    route_found = False
    unvisited_nodes = []
    node_distances = {}
    node_distances["start"] = 0
    for nodes in graph:
        unvisited_nodes.append(nodes)
    unvisited_nodes.remove(start)
    while route_found == False:
        graph_node = None
        for x in unvisited_nodes:
            if find_time(x,start,node_distances,graph) < smallest:
                smallest = find_time(x,start,node_distances,graph)
        if graph_node == destination:
            route_found == True
            return(node_distances)
        else:
            node_distances[graph_node] = "distance + route"
    pass


def reconstruct_journey(route, graph):
    """
    Given a route (list of stops), reconstruct the journey with details of each leg.
    Returns a list of tuples: (from_stop, to_stop, route, travel_time)
    (currently a placeholder for the actual implementation)
    """
    pass


def main():
    trains = get_trains("Victoria Underground Station",datetime.now(timezone.utc),datetime.now(timezone.utc),30 )

    for t in trains:
        print(t.line)
        print(t.direction)
        print(t.stops)


if __name__ == "__main__":
    main()
