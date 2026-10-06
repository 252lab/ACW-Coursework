from importlib.resources import path

import requests
import pandas as pd

# 1. Define the graph data model: 
# store each route as a list of stops.
# build graphs based on these dictionaries, where each stop is a node and each connection is an edge with a weight (travel time).
route_A = ["StopA", "StopB", "StopC", "StopD"]
route_B = ["StopE", "StopF", "StopG", "StopH"]
route_C = ["StopB", "StopD", "StopF", "StopH"]
route_D = ["StopA", "StopE", "StopG", "StopH"]

routes = [route_A, route_B, route_C, route_D]

def get_list_of_stops(routes):
    """
    Returns an ordered list of stops from the routes.
    """
    stops = []
    for route in routes:
        for i in range(len(route)):
            stops.append(route[i])
    stops = sorted(set(stops))
    return stops

def construct_graph(routes):
    """
    Construct a dictionary-based graph from a list of routes.
    Each stop is a key, and its value is a list of stops it connects to.
    (currently a placeholder!)
    """
    graph = {}
    pass
        

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
    '''
    # Example usage of the find_route function
    graph = example_graph  # Use the predefined example graph
    start = "StopA"
    destination = "StopD"
    route = find_route(graph, start, destination)
    print("Route found:", route)
    '''
    print(get_list_of_stops(routes))

if __name__ == "__main__":
    main()