import datetime
import requests
from flask import Flask, request, render_template

# setting up flask app
app = Flask(__name__)

BASE_URL = "https://api.tfl.gov.uk"

#TODO
""" 
This subroutine is used to retrieve the form inputs from the index.html page, and verify that they are valid.
If they inputs are not valid, an error message will be displayed and the user will be promted to re-enter their
inputs. If the inputs are valid, they will then be sent to the algorithm.
"""
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
        # removing any extra spaces and changing them to lowecase, to make it 
        # easier to verify
        try:
            startLocation = request.form.get("startLocation").strip()
            endLocation = request.form.get("endLocation").strip()

            # default is an empty string if no input for the time
            startTime = request.form.get("startTime", "").strip()
            endTime = request.form.get("EndTime", "").strip()
            
            # call function to validate inputs (and update then when necessary)
            startLocation, endLocation, startTime, endTime = validate_inputs(startLocation, endLocation, startTime, endTime)

            #TODO -> send to algorithm/proper backend here (Needs to handle time inputs there i think?)

        except:
            #TODO - temporary error message -> need to output html/css/js pop up
            print("Form elements cannot be retrieved")

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

#checking if the station is valid
# return station ID if found
def find_station(stationName):

    # converting the station name to lower case and removing any extra paces
    toMatch = stationName.toLower().replace(" ", "")
    foundMatches = []

    # retriving list of station names and IDs to check

    try:
        pass
    except:
        pass

    # searching array of Ids
    try:
        pass
    except:
        pass


    if (foundMatches.len() == 1):
        return foundMatches[0]
    
    elif (foundMatches.len() > 1):
        pass
        # need to handle two stations having similar names

    # find a specific stop based on its name
    # and return its ID

    # compare station common name to entered name
    # if entered name in station name (and there is only one), return station id