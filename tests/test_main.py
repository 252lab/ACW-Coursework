from datetime import datetime, timezone

import pytest
import requests

from app.main import (
    Train,
    _get_routes_for_line_cached,
    astar_step,
    get_json,
    get_station_id,
    get_trains,
    init_route,
    main,
    route_stations,
)

# Types of tests:
# Some tests marked "integration" call the live TfL API and require network access.
# Some tests marked "mock" use mocked API responses.
# Some tests marked "endtoend" simulate complete journeys through the system.
# Run offline with: pytest -m "not integration"


# TESTS FOR HELPER FUNCTIONS

@pytest.mark.integration
def test_get_json_valid_url():
    lines = get_json("/Line/Mode/tube")

    assert isinstance(lines, list)
    assert lines
    assert all(
        isinstance(line, dict) and {"id", "name", "modeName"} <= line.keys()
        for line in lines
    )


@pytest.mark.integration
def test_get_json_invalid_url():
    with pytest.raises(requests.exceptions.RequestException):
        get_json("/invalid/url")


@pytest.mark.mock
def test_get_json_timeout(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout("Timeout error")

    monkeypatch.setattr("app.main.SESSION.get", fake_get)

    with pytest.raises(requests.exceptions.RequestException):
        get_json("/Line/Mode/tube")


def test_get_station_id_short_and_full_name_match():
    full = get_station_id("Oxford Circus Underground Station")

    assert get_station_id("Oxford Circus") == full
    assert get_station_id("oxford circus") == full


def test_get_station_id_naptan_passthrough():
    assert get_station_id("940gzzluoxc") == "940GZZLUOXC"


def test_get_station_id_unknown():
    with pytest.raises(ValueError):
        get_station_id("Not A Real Station")


@pytest.mark.integration
def test_get_routes_for_line_cached_valid():
    routes = _get_routes_for_line_cached("bakerloo", "inbound")

    assert isinstance(routes, tuple)
    assert routes
    assert all(
        isinstance(route, tuple)
        and all(isinstance(stop, str) for stop in route)
        for route in routes
    )


@pytest.mark.integration
def test_get_routes_for_line_cached_invalid():
    with pytest.raises(requests.exceptions.RequestException):
        _get_routes_for_line_cached("not-a-real-line", "inbound")


# MOCK DATA FOR OFFLINE ROUTE-FINDING TESTS

MOCK_JOURNEYS = {
    "direct": {
        "start": "Start",
        "destination": "End",
        "expected_time": 12,
        "expected_stations": ["Start", "End"],
        "expected_lines": ["Red"],
        "trains": {
            "Start": [{"line": "Red", "stops": {"End": 12}}],
        },
    },
    "one_switch": {
        "start": "Start",
        "destination": "End",
        "expected_time": 20,
        "expected_stations": ["Start", "Mid", "End"],
        "expected_lines": ["Red", "Blue"],
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
        "expected_time": 40,
        "expected_stations": ["Start", "Mid1", "Mid2", "End"],
        "expected_lines": ["Red", "Green", "Blue"],
        "trains": {
            "Start": [
                {"line": "Red", "stops": {"Mid1": 4, "End": 50}},
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


START_TIME = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)


def test_get_trains_builds_each_train_without_live_predictions(monkeypatch):
    start_id = get_station_id("Baker Street")
    stop_id = get_station_id("Oxford Circus")
    destination_id = get_station_id("Bank")

    arrivals = [
        {
            "vehicleId": f"vehicle-{minute}",
            "expectedArrival": f"2026-01-01T08:{minute:02d}:00+00:00",
            "destinationNaptanId": destination_id,
            "lineId": "bakerloo",
            "naptanId": start_id,
            "lineName": "Bakerloo",
        }
        for minute in (10, 20)
    ]

    timetable = {
        "timetable": {
            "routes": [
                {
                    "stationIntervals": [
                        {
                            "intervals": [
                                {
                                    "stopId": stop_id,
                                    "timeToArrival": 4,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    def fake_get_json(path):
        if path.startswith("/StopPoint/"):
            return arrivals
        return timetable

    monkeypatch.setattr("app.main.get_json", fake_get_json)
    monkeypatch.setattr("app.main.get_vehicle_predictions", lambda _: [])

    trains = get_trains("Baker Street", START_TIME, START_TIME)

    assert len(trains) == 2
    assert [train.stops[0][stop_id] for train in trains] == [14, 24]


def make_fake_get_trains(trains_by_station):
    """Build get_trains stand-ins from a small mock journey graph."""

    def fake_get_trains(station, start_time, arrival_time, minutes=30):
        boarding_minutes = round(
            (arrival_time - start_time).total_seconds() / 60
        )

        trains = []
        for spec in trains_by_station.get(station, []):
            train = Train()
            train.line = spec["line"]
            train.vehicle_id = spec["line"]
            train.direction = "inbound"
            train.stops = [
                {
                    name: boarding_minutes + ride
                    for name, ride in spec["stops"].items()
                }
            ]
            trains.append(train)

        return trains

    return fake_get_trains


def test_main_normalizes_station_names_to_ids(monkeypatch):
    start_id = get_station_id("Baker Street")
    end_id = get_station_id("Bank")

    mock_trains = make_fake_get_trains(
        {
            start_id: [
                {
                    "line": "Mock",
                    "stops": {end_id: 12},
                }
            ]
        }
    )

    monkeypatch.setattr("app.main.get_trains", mock_trains)
    monkeypatch.setattr(
        "app.main.get_stations_lon_lat_dictionary",
        lambda: {},
    )

    route = main("Baker Street", "Bank", START_TIME)

    assert route is not None
    assert route.route_complete
    assert route_stations(route) == [start_id, end_id]


@pytest.mark.endtoend
@pytest.mark.parametrize("name", MOCK_JOURNEYS)
def test_journeys(name, monkeypatch):
    journey = MOCK_JOURNEYS[name]

    monkeypatch.setattr(
        "app.main.get_trains",
        make_fake_get_trains(journey["trains"]),
    )
    monkeypatch.setattr(
        "app.main.get_station_id",
        lambda station: station,
    )
    monkeypatch.setattr(
        "app.main.get_stations_lon_lat_dictionary",
        lambda: {},
    )

    route = main(
        journey["start"],
        journey["destination"],
        START_TIME,
    )

    assert route is not None
    assert route.route_complete
    assert route.current_time == journey["expected_time"]
    assert route_stations(route) == journey["expected_stations"]
    assert [train.line for train in route.trains] == journey["expected_lines"]


@pytest.mark.endtoend
def test_faster_route_one_switch(monkeypatch):
    journey = {
        "Start": [
            {
                "line": "Red",
                "stops": {"Mid": 5, "End": 40},
            }
        ],
        "Mid": [
            {
                "line": "Blue",
                "stops": {"End": 10},
            }
        ],
    }

    monkeypatch.setattr(
        "app.main.get_trains",
        make_fake_get_trains(journey),
    )
    monkeypatch.setattr(
        "app.main.get_station_id",
        lambda station: station,
    )
    monkeypatch.setattr(
        "app.main.get_stations_lon_lat_dictionary",
        lambda: {},
    )

    route = main("Start", "End", START_TIME)

    assert route is not None
    assert route.route_complete
    assert route.current_time == 20
    assert route_stations(route) == ["Start", "Mid", "End"]
    assert [train.line for train in route.trains] == ["Red", "Blue"]


@pytest.mark.endtoend
def test_faster_route_two_switches(monkeypatch):
    journey = {
        "Start": [
            {
                "line": "Red",
                "stops": {"Mid1": 4, "End": 60},
            }
        ],
        "Mid1": [
            {
                "line": "Green",
                "stops": {"Mid2": 8, "End": 35},
            }
        ],
        "Mid2": [
            {
                "line": "Blue",
                "stops": {"End": 18},
            }
        ],
    }

    monkeypatch.setattr(
        "app.main.get_trains",
        make_fake_get_trains(journey),
    )
    monkeypatch.setattr(
        "app.main.get_station_id",
        lambda station: station,
    )
    monkeypatch.setattr(
        "app.main.get_stations_lon_lat_dictionary",
        lambda: {},
    )

    route = main("Start", "End", START_TIME)

    assert route is not None
    assert route.route_complete
    assert route.current_time == 40
    assert route_stations(route) == [
        "Start",
        "Mid1",
        "Mid2",
        "End",
    ]
    assert [train.line for train in route.trains] == [
        "Red",
        "Green",
        "Blue",
    ]
