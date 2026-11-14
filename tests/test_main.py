from datetime import datetime, timezone

import pytest
import requests

from python.main import (
    Route,
    Train,
    access_stop_point,
    astar_step,
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
# Run offline with: pytest -m "not integration" 

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
    assert all(isinstance(line, dict) and {"id", "name", "modeName"} <= line.keys() for line in lines)


@pytest.mark.integration
def test_get_json_invalid_url():
    """
    Test the get_json function with an invalid URL.
    """
    with pytest.raises(requests.exceptions.RequestException):
        get_json("/invalid/url")


@pytest.mark.mock()
def test_get_json_timeout(monkeypatch):
    """
    Test that get_json lets a timeout from requests through.
    Uses monkeypatch for mocking.
    """
    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout("Timeout error")

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(requests.exceptions.RequestException):
        get_json("/Line/Mode/tube")


# create mock data for small-scale end-to-end tests

MOCK_JOURNEYS = {
    "direct": {
        "start": "Start",
        "destination": "End",
        "trains": {
            "Start": [{"line": "Red", "stops": {"End": 12}}],
        },
    },
    "one_switch": {
        "start": "Start",
        "destination": "End",
        "trains": {
            "Start": [
                {"line": "Red", "stops": {"Mid": 5, "End": 25}},
            ],
            "Mid": [
                {"line": "Blue", "stops": {"End": 10}},
            ],
        },
    },
    "two_switches": {
        "start": "Start",
        "destination": "End",
        "trains": {
            "Start": [
                {"line": "Red", "stops": {"Mid1": 4, "End": 40}},
            ],
            "Mid1": [
                {"line": "Green", "stops": {"Mid2": 8}},
            ],
            "Mid2": [
                {"line": "Blue", "stops": {"End": 18}},
            ],
        },
    },
}


@pytest.mark.endtoend
def test_one_valid_direct_route():
    """
    Test a journey with one valid direct route.
    Uses sample data on a small graph that can be checked by hand.
    """
    python.main(MOCK_JOURNEYS["direct"]["start"], MOCK_JOURNEYS["direct"]["destination"], MOCK_JOURNEYS["direct"]["trains"])
    
    


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
