import datetime
import flask

# used just for setting function up
from flask import Flask, request, render_template
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
            startLocation = request.form.get("startLocation").strip().toLower()
            endLocation = request.form.get("endLocation").strip().toLower()

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
        #TODO - Change error message later
        print("Couldn't validate time inputs.")
    
    # returning the validated inputs
    return startLocation, endLocation, startTime, endTime