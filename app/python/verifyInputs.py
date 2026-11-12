import datetime
import requests
from main import *

BASE_URL = "https://api.tfl.gov.uk"

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
    listStations = list_stations()

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

def list_stations():
    #retriving array of stop points and ids
    return []

