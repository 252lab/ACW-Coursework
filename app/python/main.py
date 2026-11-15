import requests
import pandas as pd
import numpy
import flask
from flask_frozen import Freezer
import datetime
from flask import Flask, redirect, url_for, render_template

# used just for setting function up
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__,template_folder="../templates")
freezer = Freezer(app)

BASE_URL = "https://api.tfl.gov.uk"

# rendering the starting page
@app.route("/")
def index():
    return render_template("index.html")

# rendering the loading page
@app.route("/loading")
def loading():
    return render_template("loading.html")

# rendering the route page
@app.route("/route")
def route():
    return render_template("route.html")

#switching to index page
def to_index():
    return redirect(url_for('index.html'))

# switching to loading page
def to_loading():
    return redirect(url_for('loading.html'))

# switching to route page
def to_route():
    return redirect(url_for('route.html'))


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


""" 
This subroutine is used to retrieve the form inputs from the index.html page, and verify that they are valid.
If they inputs are not valid, an error message will be displayed and the user will be promted to re-enter their
inputs. If the inputs are valid, they will then be sent to the algorithm.
"""
@app.route("/route_input", methods=["GET", "POST"])
def route_input():

    # switching to loading page while back end is running
    to_loading()

    # initialising input variables
    startLocation = ""
    endLocation = ""
    startTime = ""
    endTime = ""

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
            endTime = request.form.get("endTime", "").strip()
            
            # call function to validate inputs (and update then when necessary)
            startLocation, endLocation, startTime, endTime = validate_inputs(startLocation, endLocation, startTime, endTime)

            #TODO -> send to algorithm/proper backend here (Needs to handle time inputs there i think?)
            # send to route page
            #return redirect(url_for('route.html'))
            render_template("route.html")

        except:
            #TODO - temporary error message -> need to output html/css/js pop up
            #Send back to index page
            print("Form elements cannot be retrieved")
            to_index()

# function used to check if stations can be matched to API - TODO
# also checks that the user has only entered one of the start and end time
def validate_inputs(startLocation, endLocation, startTime, endTime):

    # variable to check if the inputs are valid
    validInputs = True

    # assigning variables
    startID = ""
    endID = ""
    
    #validating station names
    try:
        # check if start station and end station can be found in the API/data
        #TODO -> implement searching algorithm (either sort the data and use binary search, or use Boyer Moore Algorithm for Pattern Searching)

        if (startLocation == endLocation):
            #TODO -> update error message
            print("Please enter two different stations.")
            validInputs = False
        else:

            startID = find_station(startLocation)
            endID = find_station(endLocation)

            if (startID == -1 or endID == -1):
                validInputs = False
                #TODO - ERROR MESSAGE
                print("One or both of your stations could not be found")

    except:
        #TODO -> update with proper error message later
        print("Your entered stations could not be found.")
        validInputs = False
    
    # validating time inputs
    try:
        # if both times are entered, output an error message
        if (startTime != "" and endTime != ""):
            #TODO - change to proper error message
            print("Please only enter one time.")
            validInputs = False

        # if no time is entered, get the current time as the start time
        elif (startTime == "" and endTime == ""):
            startTime = datetime.now()
    except:
        #TODO - Change error message later
        print("Couldn't validate time inputs.")
        validInputs = False

    # if all the inputs thaty have been entered are valid
    if validInputs:
        # returning the validated inputs
        return startID, endID, startTime, endTime
    else:
        pass 
        #TODO - ERROR MESSAGE

#checking if the station is valid
# return station ID if found
def find_station(stationName):

    # converting the station name to lower case and removing any extra paces
    toMatch = stationName.lower().replace(" ", "")
    found = False

    # getting array of stations
    listStations = list_stations()

    # searching the array of stations fopr a match
    try:
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
        print("Something went wrong")

# returning the list of stations
def list_stations():
    
    # filepath for csv file
    filepath = "/tfl-stationdata-detailed/Stations.csv"

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
        tube_names[i][0].lower().replace(" ", "")

    # returning list of stations
    return tube_names

def error_found(message):
    pass
# use flask flash funtion
# return html code with error message 
# switch back to index page

if __name__ == "__main__":
    freezer.freeze()

