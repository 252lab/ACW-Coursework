from importlib.resources import path

import pandas as pd
import requests

def get_routes_between_two_stops_from_api(start, destination):
    '''
    Fetch all bus routes from the TFL API and filter them to find routes that connect the start and destination stops.
    Returns a dictionary of relevant routes with their stop sequences.
    '''
    # Fetch all bus routes from the TFL API
    all_routes = get_bus_routes()
    relevant_routes = {}
    # Filter routes that contain either the start or destination stop, or both
    for route in all_routes:
        route_id = route.get("id")
        # fetch the stop points for this route
        try:
            route_sequence = get_json(f"/Line/{route_id}/Route/Sequence")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching stop points for route {route_id}: {e}")
            continue
        # Add the route to relevant_routes if it contains both start and destination
        if start in route_sequence or destination in route_sequence:
            relevant_routes[route_id] = route_sequence
    return relevant_routes

#creates a list of one-value dictionaries
#the line is the key, and the value is a list of dictionaries containing the inbound and outbound stop lists
def get_list_of_lines():
    #list of valid tube lines
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
        line_list = {line:[]}
        for direction in ["inbound","outbound"]:#get the inbound/outbound list as separate
            url = "https://api.tfl.gov.uk/Line/"+line+"/Route/Sequence/"+direction
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
            else:
                raise Exception("API not responding")
            naptanids = data["orderedLineRoutes"][0]["naptanIds"]
            direction_stop_list = {direction:naptanids}
            line_list[line].append(direction_stop_list)
        stop_list.append(line_list)
    return(stop_list)

print(get_list_of_lines())



get_list_of_lines()
def get_list_of_stops(routes):
    """
    Returns an ordered list of stops from the routes.
    """
    stops = []
    routes = get_routes_between_two_stops_from_api(start, destination).values()
    for route in routes:
        for i in range(len(route)):
            stops.append(route[i])
    stops = sorted(set(stops))
    return stops

def construct_graph(routes, stops):
    """
    Construct a dictionary-based graph from a list of routes.
    Each stop is a key, and its value is a list of stops it connects to.
    Not allowing bidirectional travel.
    """
    graph = {}
    stops = get_list_of_stops(start, destination)
    for stop in stops:
        graph[stop] = []
    for route in routes:
        for i in range(len(route) - 1):
            graph[route[i]].append(route[i + 1])
    # remove any duplicates 
    for stop in graph:
        graph[stop] = list(sorted(set(graph[stop])))
    return graph

# 2. Implement shortest-time route search
# Add find_route(graph, start, destination) using Dijkstra’s algorithm / A* algorithm.
# Ensure it returns the fastest path and its total estimated time.
def find_route(graph, start, destination):
    """
    Find a route from start to destination using the A* algorithm.
    This function should return a list of nodes representing the path from start to destination.
    (currently a placeholder for the actual implementation)
    """
    pass

# 3. Reconstruct and report the journey
# Return all the bus stops along the journey, and the time taken between each.
# It should be a sequence of steps.
def reconstruct_journey(route, graph):
    """
    Given a route (list of stops), reconstruct the journey with details of each leg.
    Returns a list of tuples: (from_stop, to_stop, route, travel_time)
    (currently a placeholder for the actual implementation)
    """
    pass

# 5. Load graph data from TfL
# Fetch ordered route stop sequences and convert them into a graph format. 

BASE_URL = "https://api.tfl.gov.uk"

def get_json(path):
    """
    Fetch BASE_URL + path and return the JSON response.
    Raise requests.exceptions.RequestException for any request errors.
    """
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

def get_bus_routes():
    """
    Fetch all bus routes from the TFL API.
    Returns a list of bus route dictionaries.
    """
    return get_json("/Line/Mode/bus")

def get_stop_point(stop_point_id):
    """
    Fetch a specific stop point from the TFL API.
    Returns a dictionary containing the stop point details.
    """
    return get_json(f"/StopPoint/{stop_point_id}")

def access_stop_point():
    """
    Access a specific stop point and print its keys.
    """
    try:
        stop = get_stop_point("490008660N")  # Example stop point ID
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stop point: {e}")
        return
    print(stop.keys())

def main():
    # Example usage of the find_route function
    graph = example_graph  # Use the predefined example graph
    start = "StopA"
    destination = "StopD"
    route = find_route(graph, start, destination)
    print("Route found:", route)

if __name__ == "__main__":
    main()