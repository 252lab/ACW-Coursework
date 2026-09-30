import requests
import pandas as pd

BASE_URL = "https://api.tfl.gov.uk"

# filters to only bus routes, doesn't include other modes of transport
bus_route_url = BASE_URL + "/Line/Mode/bus"

# make the api call
try:
    response = requests.get(bus_route_url)
    response.raise_for_status()  # Raise an error for bad responses 
    # get the raw JSON response
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

def get_routes_from_start_point(start_point_id):
    specific_start_point_url = f"{BASE_URL}/StopPoint/{start_point_id}"
    try:
        response = requests.get(specific_start_point_url)
        response.raise_for_status()  # Raise an error for bad responses 
        # get the raw JSON response
        start_point_data = response.json()
        return start_point_data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

routes_example = get_routes_from_start_point("490008660N")  # Example start point ID
print(routes_example)