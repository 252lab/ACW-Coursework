from datetime import datetime, timezone

import pytest
import requests

from app.main import (
    TfLAPIError,
    Train,
    Route,
    _get_routes_for_line_cached,
    get_station_order,
    heuristic,
    get_json,
    get_station_id,
    get_timetable,
    get_trains,
    main,
    route_stations,
    app as flask_app,
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
    with pytest.raises(TfLAPIError, match="HTTP 404"):
        get_json("/invalid/url")


@pytest.mark.mock
def test_get_json_timeout(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout("Timeout error")

    monkeypatch.setattr("app.main.SESSION.get", fake_get)

    with pytest.raises(TfLAPIError, match="timed out"):
        get_json("/Line/Mode/tube")


@pytest.mark.parametrize("status_code", [404, 500, 503])
def test_get_timetable_logs_and_skips_unavailable_responses(
    monkeypatch, caplog, status_code
):
    def fake_get_json(_path):
        raise TfLAPIError("Timetable unavailable", status_code=status_code)

    monkeypatch.setattr("app.main.get_json", fake_get_json)
    get_timetable.cache_clear()

    with caplog.at_level("WARNING", logger="app.main"):
        assert get_timetable("bakerloo", "from", "to") is None

    assert "status=" + str(status_code) in caplog.text
    assert "/Line/bakerloo/Timetable/from/to/to" in caplog.text

    get_timetable.cache_clear()


def test_get_timetable_propagates_rate_limit_errors(monkeypatch):
    def fake_get_json(_path):
        raise TfLAPIError("Rate limited", status_code=429)

    monkeypatch.setattr("app.main.get_json", fake_get_json)
    get_timetable.cache_clear()

    with pytest.raises(TfLAPIError, match="Rate limited") as error:
        get_timetable("bakerloo", "from", "to")

    assert error.value.status_code == 429
    get_timetable.cache_clear()


def test_route_input_displays_tfl_api_error(monkeypatch):
    monkeypatch.setattr(
        "app.main.validate_inputs",
        lambda *_: ("START", "END", START_TIME),
    )

    def raise_api_error(*_):
        raise TfLAPIError("TfL's live station arrivals service is unavailable.")

    monkeypatch.setattr("app.main.main", raise_api_error)
    monkeypatch.setitem(flask_app.config, "TESTING", True)

    response = flask_app.test_client().post(
        "/route_input",
        data={"startLocation": "Start", "endLocation": "End"},
        follow_redirects=True,
    )

    assert b"TfL&#39;s live station arrivals service is unavailable." in response.data


def test_get_station_id_short_and_full_name_match():
    full = get_station_id("Oxford Circus Underground Station")

    assert get_station_id("Oxford Circus") == full
    assert get_station_id("oxford circus") == full


def test_get_station_id_common_aliases():
    assert get_station_id("Kings Cross") == get_station_id(
        "King's Cross St. Pancras Underground Station"
    )
    assert get_station_id("Heathrow Terminals 1, 2 and 3") == get_station_id(
        "Heathrow Terminals 2 & 3 Underground Station"
    )


def test_get_station_id_fuzzy_match():
    assert get_station_id("Oxford Cirkus") == get_station_id("Oxford Circus")


def test_get_station_id_rejects_ambiguous_name():
    with pytest.raises(ValueError, match="Ambiguous station name"):
        get_station_id("Hammersmith")


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
    with pytest.raises(TfLAPIError) as error:
        _get_routes_for_line_cached("not-a-real-line", "inbound")

    assert error.value.status_code == 404


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


def test_main_returns_none_when_destination_is_unreachable(monkeypatch):
    trains = make_fake_get_trains({
        "Start": [
            {
                "line": "Red",
                "stops": {"DeadEnd": 5},
            }
        ],
    })

    monkeypatch.setattr(
        "app.main.get_station_id",
        lambda station: station,
    )
    monkeypatch.setattr("app.main.get_trains", trains)
    monkeypatch.setattr(
        "app.main.get_stations_lon_lat_dictionary",
        lambda: {},
    )

    route = main("Start", "End", START_TIME)

    assert route is None

def test_heuristic_is_zero_for_dijkstra():
    assert heuristic("A", "B", {}, "dijkstra") == 0


def test_heuristic_is_zero_when_coordinates_are_missing():
    assert heuristic("A", "B", {}, "euclidean") == 0

def test_get_station_order_filters_unknown_stations():
    timetable = {
        "timetable": {
            "routes": [
                {
                    "stationIntervals": [
                        {
                            "intervals": [
                                {
                                    "stopId": "940GZZLUOXC",
                                    "timeToArrival": 4,
                                },
                                {
                                    "stopId": "UNKNOWN",
                                    "timeToArrival": 5,
                                },
                            ]
                        }
                    ]
                }
            ]
        }
    }

    groups = get_station_order(timetable)

    assert groups == [[("940GZZLUOXC", 4)]]

def test_main_does_not_loop_back_to_start(monkeypatch):
    journey = {
        "Start": [
            {"line": "Red", "stops": {"Mid": 5}},
        ],
        "Mid": [
            {"line": "Red", "stops": {"Start": 3}},
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

    assert route is None


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
