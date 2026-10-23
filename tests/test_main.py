# Placeholder test file for the main.py module. Add test cases here.
import pytest
import requests

from python.main import get_json, get_tube_routes, get_stop_point, access_stop_point, get_routes_for_line, get_list_of_lines, get_list_of_stops

# TESTS FOR HELPER FUNCTIONS 

# These tests call the live TfL API and require network access.
pytestmark = pytest.mark.integration

# get_json tests

def test_get_json_valid_url():
    """
    Test the get_json function with a valid URL.
    """
    lines = get_json("/Line/Mode/tube")
    assert isinstance(lines, list)
    assert lines
    assert all(
        isinstance(line, dict)
        and {"id", "name", "modeName"} <= line.keys()
        for line in lines
    )

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
    assert all(
        isinstance(route, dict) and {"id", "name"} <= route.keys()
        for route in routes
    )

# get_stop_points routes

def test_get_stop_points():
    """
    Test the get_stop_points function with a valid stop point ID.
    TODO: Needs fixing.
    """
    response = get_stop_point(f"/StopPoint/490008660N")
    assert {"id", "commonName"} <= response.keys() in response

def test_get_stop_points_invalid():
    """
    Test the get_stop_points function with an invalid stop point ID.
    """
    with pytest.raises(requests.exceptions.RequestException):
        get_stop_point(f"/StopPoint/invalid_id")

def test_access_stop_point():
    """
    Test the access_stop_point function with a valid stop ID.
    """
    keys = access_stop_point(f"/StopPoint/490008660N")
    assert {"id", "commonName"} in keys


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

