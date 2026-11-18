
# imports 
import requests
import pandas as pd
import numpy
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup
import secrets


app = Flask(__name__,template_folder="templates")

# generating secret key
secret_key = secrets.token_hex(16)
app.config['SECRET_KEY'] = secret_key

BASE_URL = "https://api.tfl.gov.uk"

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

        except:
             message = "Form elements cannot be retrieved."
             return error_found(message)
                    
        return to_route()



# function used to check if stations can be matched to API - TODO
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
    route_output = ""

    try:

        #TODO - set up route output

        # switching to the route page
        return render_template("route.html", injected_html=Markup(route_output))

    # catches anything that goes wrong
    except:
        message = "Something went wrong."
        error_found(message)
    

if __name__ == "__main__":
    app.run(debug=True)
