import pytest
import requests

from python.main import (
    access_stop_point,
    get_json,
    get_list_of_lines,
    get_list_of_stops,
    get_routes_for_line,
    get_stop_point,
    get_tube_routes,
)

# Types of tests:
# Some of the tests are marked as "integration" tests: these tests call the live TfL API and require network access.
# Some of the tests are marked as "mock" tests: these tests use mocked responses to simulate the TfL API and do not require network access.
# Some of the tests are marked as "endtoend" tests: these tests simulate a full user journey through the system. 

# ------------------------------------------------------------------------------------------------------

# TESTS FOR HELPER FUNCTIONS

# get_json tests ---------------------------------------------------------------------------------------

@pytest.mark.integration
def test_get_json_valid_url():
    """
    Test the get_json function with a valid URL.
    """
    lines = get_json("/Line/Mode/tube")
    assert isinstance(lines, list)
    assert lines
    assert all(
        isinstance(line, dict) and {"id", "name", "modeName"} <= line.keys() for line in lines
    )

@pytest.mark.integration
def test_get_json_invalid_url():
    """
    Test the get_json function with an invalid URL.
    """
    with pytest.raises(requests.exceptions.RequestException):
        get_json("/invalid/url")

@pytest.mark.skip(reason="A deterministic timeout test needs a mocked request.")
def test_get_json_timeout():
    """
    Test the get_json function with a timeout.
    """
    # Skipped until we can test this without mocking or relying on a flaky live timeout.

# ----------------------------------------------------------------

# get_tube_routes tests


@pytest.mark.integration
def test_get_tube_routes_valid():
    """
    Test the get_tube_routes function to ensure it returns a list of tube routes.
    """
    routes = get_tube_routes()
    assert isinstance(routes, list)
    assert routes
    assert all(isinstance(route, dict) and {"id", "name"} <= route.keys() for route in routes)


# get_stop_points tests


@pytest.mark.integration
def test_get_stop_point_valid():
    """
    Test the get_stop_point function with a valid stop point ID.
    """
    response = get_stop_point("490008660N")
    assert isinstance(response, dict)
    assert {"id", "commonName"} <= set(response.keys())


@pytest.mark.integration
def test_get_stop_point_invalid_id():
    """
    Test the get_stop_points function with an invalid stop point ID.
    """
    with pytest.raises(requests.exceptions.RequestException):
        get_stop_point("invalid_id")


# get_access_stop_point tests


@pytest.mark.integration
def test_access_stop_point_valid_id():
    """
    Test the access_stop_point function with a valid stop ID.
    """
    keys = access_stop_point("940GZZDLABR")
    assert {"id", "commonName"} <= keys


@pytest.mark.integration
def test_access_stop_point_invalid_id():
    """
    Test the access_stop_point function with an invalid stop ID.
    """
    result = access_stop_point("invalid_id")
    assert result is None


# get_routes_for_line tests


@pytest.mark.integration
def test_get_routes_for_line_valid():
    """
    Test the get_routes_for_line function to check that it returns a list of naptanIds for a valid line from the TFL API
    """
    routes = get_routes_for_line("bakerloo", "inbound")
    assert isinstance(routes, list)
    assert routes
    assert all(isinstance(route, list) and all(isinstance(stop, str) for stop in route) for route in routes)


@pytest.mark.integration
def test_get_routes_for_line_invalid():
    """
    Test the get_routes_for_line function to check that an error is raised for an invalid line.
    """
    with pytest.raises(requests.exceptions.RequestException):
        get_routes_for_line("not-a-real-line", "inbound")


# get_list_of_lines tests

@pytest.mark.integration
def test_get_list_of_lines_valid():
    """
    Test the get_list_of_lines function to ensure it returns a list of one-value dictionaries.
    """
    lines = get_list_of_lines()
    assert isinstance(lines, list)
    assert lines
    assert len(lines) == 11

    for line in lines:
        assert isinstance(line, dict)
        assert len(line) == 1
        directions = next(iter(line.values()))
        assert isinstance(directions, list)
        assert [list(direction) for direction in directions] == [["inbound"], ["outbound"]]
        assert all(
            isinstance(stops, list) and stops and all(isinstance(stop, str) for stop in stops)
            for direction in directions
            for stops in direction.values()
        )


# get_list_of_stops tests

def test_get_list_of_stops():
    routes = [
        ["bakerloo", "paddington", "oxford"],
        ["paddington", "notting-hill", "central"],
        ["central", "bakerloo", "queen's-park"],
    ]
    stops = get_list_of_stops(routes)
    expected = sorted({stop for route in routes for stop in route})
    assert isinstance(stops, list)
    assert stops
    assert stops == expected

def test_get_list_of_stops_empty():
    routes = []
    stops = get_list_of_stops(routes)
    assert isinstance(stops, list)
    assert stops == []


# To be filled in with actual test cases for the main.py functions. The following are placeholders for future tests.
@pytest.mark.endtoend
def test_one_valid_direct_route():
    """
    Test a journey with one valid direct route.
    """
    pass


@pytest.mark.endtoend
def test_faster_route_one_switch():
    """
    Test a journey that requires one switch to reach the destination faster.
    """
    pass


@pytest.mark.endtoend
def test_faster_route_two_switches():
    """
    Test a journey that requires two switches to reach the destination faster.
    """
    pass
