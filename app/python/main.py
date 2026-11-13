import requests
import pandas as pd
import flask
from flask_frozen import Freezer
from verifyInputs import *

# used just for setting function up
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)
freezer = Freezer(app)

BASE_URL = "https://api.tfl.gov.uk"

@app.route("/")
def index():
    return render_template("index.html")


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
""" 
This subroutine is used to retrieve the form inputs from the index.html page, and verify that they are valid.
If they inputs are not valid, an error message will be displayed and the user will be promted to re-enter their
inputs. If the inputs are valid, they will then be sent to the algorithm.
"""
@app.route("/route_input", methods=["GET", "POST"])
def route_input():

    #TODO: Call loading page here!!!

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
            startLocation = request.form.get("startLocation").strip()
            endLocation = request.form.get("endLocation").strip()

            # default is an empty string if no input for the time
            startTime = request.form.get("startTime", "").strip()
            endTime = request.form.get("endTime", "").strip()
            
            # call function to validate inputs (and update then when necessary)
            startLocation, endLocation, startTime, endTime = validate_inputs(startLocation, endLocation, startTime, endTime)

            #TODO -> send to algorithm/proper backend here (Needs to handle time inputs there i think?)
            # send to route page
            return redirect(url_for('route.html'))

        except:
            #TODO - temporary error message -> need to output html/css/js pop up
            #Send back to index page
            print("Form elements cannot be retrieved")
            return render_template('index.html')


if __name__ == "__main__":
    freezer.freeze()