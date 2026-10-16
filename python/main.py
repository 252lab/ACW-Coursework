import requests
import pandas as pd
import datetime

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


#TODO
# function used to retrieve form inputs
# likely need to restructure app but do that when merge with back end properly
@app.route("/", methods=["GET", "POST"])
def route_input():


    # initialising input variables
    startLocation = ""
    endLocation = ""
    startTime = ""
    endTime = ""

    # if the form request method is post
    if request.method("POST"):

        # try to get the form inputs
        try:
            startLocation = request.form.get("startLocation")
            endLocation = request.form.get("endLocation")
            startTime = request.form.get("startTime")
            endTime = request.form.get("EndTime")
            
            # call function to validate inputs
            validate_inputs(startLocation, endLocation, startTime, endTime)

            # otherwise output an error
            # need to send inputs to function to handle them
            # remember to switch html page
        except:
            #TODO - temporary error message -> need to output html/css/js pop up
            print("Form elements cannot be retrieved")

# function used to check if stations can be matched to API - TODO
# also checks that the user has only entered one of the start and end time
def validate_inputs(startLocation, endLocation, startTime, endTime):
    
    #validating station names
    try:
        # check if start station and end station can be found in the API/data
        pass
    except:
        #update with proper error message later
        print("Your entered stations could not be found.")
    
    # validating time inputs
    try:
        if (startTime != "" and endTime != ""):
            #TODO - change to proper error message
            print("Please only enter one time.")
            
        elif (startTime == "" and endTime == ""):
            # take start time as current time
            startTime = datetime.now()
            # and end time as ASAP -> Don't assign?
    except:
        #Change error message later
        print("Couldn't validate time inputs.")
        
    # call algorithm function with stops and time
        
    #TODO send data to algorithm

if __name__ == "__main__":
    main()