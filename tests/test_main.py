# Placeholder test file for the main.py module. Add test cases here.
import pytest
import requests

from python.main import get_json, get_tube_routes, get_routes_for_line, get_list_of_lines, get_list_of_stops

# TESTS FOR HELPER FUNCTIONS 

# get_json tests 

def test_get_json_valid_url():
    """
    Test the get_json function with a valid URL.
    """
    lines = get_json("/Line/Mode/tube")
    assert isinstance(lines, list)
    assert lines
    assert {"id", "name", "modeName"} <= lines[0].keys()

def test_get_json_invalid_url():
    """
    Test the get_json function with an invalid URL.
    """
    with pytest.raises(requests.exceptions.RequestException):
        get_json("/invalid/url")

# get_tube_routes tests

def test_get_tube_routes():
    """
    Test the get_tube_routes function with a valid line.
    """
    routes = get_tube_routes()
    assert isinstance(routes, list)
    assert routes
    assert {"$type", "id", "name"} <= routes[0].keys()


# To be filled in with actual test cases for the main.py functions. The following are placeholders for future tests.
def test_one_valid_direct_route():
    """
    Test a journey with one valid direct route.
    """
    pass

def test_faster_route_one_switch():
    """
    Test a journey that requires one switch to reach the destination faster.
    """
    pass

def test_faster_route_two_switches():
    """
    Test a journey that requires two switches to reach the destination faster.
    """
    pass

