import requests
import pandas as pd

# used just for setting function up
from flask import Flask, request, render_template
app = Flask(__name__)

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
    return get_json(f"/StopPoint/{stop_point_id}")

def main():
    try:
        stop = get_stop_point("490008660N")  # Example stop point ID
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stop point: {e}")
        return
    print(stop.keys())

# function used to retrive form inputs
# likely need to restructure app but do that when merge with back end properly
# WIP - need to handle required inputs/not required inputs
@app.route("/", methods=["GET", "POST"])
def route_input():

    # if the form request method is post
    if request.method("POST"):

        # try to get the form inputs
        try:
            startLocation = request.form.get("startLocation")
            endLocation = request.form.get("endLocation")
            startTime = request.form.get("startTime")
            endTime = request.form.get("EndTime")

            # otherwise output an error

            # need to send inputs to function to handle them
            # remember to swtich html page
        except:
            print("Form elements cannot be retrived")

if __name__ == "__main__":
    main()