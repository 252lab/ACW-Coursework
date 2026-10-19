import requests

BASE_URL = "https://api.tfl.gov.uk"


def get_json(path):
    """
    Fetch BASE_URL + path and return the JSON response.
    Raise requests.exceptions.RequestException for any request errors.
    """
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()


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
    Access a specific stop point and print its keys.
    """
    try:
        stop = get_stop_point(stop_point_id)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stop point: {e}")
        return
    print(stop.keys())


def get_routes_for_line(line_id: str, direction: str) -> list[list[str]]:
    """
    Fetch all routes for a specific line from the TFL API.
    Returns a list of naptanIds for each route in the specified direction (inbound or outbound).
    """
    response = get_json(f"/Line/{line_id}/Route/Sequence/{direction}")
    orderedLineRoutes = response.get("orderedLineRoutes", [])
    return [route.get("naptanIds", []) for route in orderedLineRoutes]


def get_routes_between_two_stops_from_api(start, destination):
    """
    Fetch all tube routes from the TFL API and filter them to find routes that connect the start and destination stops.
    Return a dictionary of relevant routes with their stop sequences.
    NOTE: This only works for max. one switch between lines. If the route requires more than one switch, it will not be found.
    TODO: Rewrite this function to include a more robust pathfinding algorithm that can handle multiple line switches and find the optimal route.
    TODO: Or scrap this function entirely?
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
    result = get_routes_for_line("victoria", "outbound")
    print(len(result), result[0][:5])


if __name__ == "__main__":
    main()
