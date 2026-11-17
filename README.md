# ECM3428 — London Route Planner

The project is focused on developing a route-planning website for journeys in London, using the A* algorithm.

(NOTE: add more details once the project is finished)

## Problem and intended users

Finding a the most efficient public-transport route can require comparing possible connections and journey times. This project aims to let a user provide a start stop, end stop, and a start or end time, and have the program calculate the more efficient route for them.

**Intended users:** People travelling around London who want help planning the most efficient journey along the tube network.

**Current scope:** The project uses London tube stations. The station-coordinate helper filters for Underground NAPTAN IDs.

## Selected algorithm

This project uses A\* algorithm. A\* ranks a candidate station using the journey cost so far, $g(n)$, plus an estimate of the remaining cost to the destination, $h(n)$:

$$f(n) = g(n) + h(n)$$

### Algorithm outline

(NOTE: Fill this in once the project has been finished.)

### Complexity

(NOTE: analuyse the space-time complexity once the project has been finished)

## Installation

### Requirements

- Python 3 (the project has been used with Python 3.12)
- Internet access for live TfL API requests and integration tests
- Git, if cloning the repository

### Set up the Python environment

From the repository root:

**Linux / macOS (bash or zsh)**

```sh
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

Install the dependencies:

```sh
python -m pip install -r requirements.txt
```

## Access and running

- **Hosted website:** [https://252lab.github.io/ACW-Coursework](https://252lab.github.io/ACW-Coursework)

(TODO: connect the backend to the frontend)

## Testing

Run tests from the repository root with the virtual environment activated:

```sh
python -m pytest -m "not integration"
```

This excludes tests marked `integration`, which call the live TfL API. Run the entire suite, including those tests, with:

```sh
python -m pytest
```

### Test cases

The current backend tests include:

- TfL JSON request timeout handling (mocked).
- Station-name normalization, NAPTAN-ID passthrough, and unknown station handling.
- TfL line-route sequence retrieval (integration tests).
- Small mocked route graphs for direct, one-transfer, and two-transfer journeys.
- A mocked check that a station name supplied to `main()` is converted to a NAPTAN ID.

## Dependencies and third-party resources

Python packages are listed in [requirements.txt](requirements.txt):

- **requests:** HTTP requests to TfL.
- **pandas:** reading station-coordinate CSV data.
- **geopy:** geographic distance calculations for the heuristic.
- **pytest:** automated tests.
- **Flask:** backend/web integration.
- **Playwright:** frontend testing
- **ruff**, **black**, **flake8**, and **isort** - linters

External data and services:

- [TfL Unified API](https://api.tfl.gov.uk/): arrivals, timetables, and route data.
- `python/naptan.json` and files under `tfl-stationdata-detailed/`: local station metadata and coordinates.

## Known limitations and work remaining

- Route-search behavior and the A\* heuristic have not yet been fully validated; confirm heuristic units match the journey-time units.
- Transfer/waiting-time calculation and use of live arrival predictions need verification.
- The station-coordinate CSV path is currently relative to the process working directory and can fail when launched from the repository root.
- Route-journey tests currently fail because of that CSV path; the two faster-route test functions are placeholders.
- The current website is a prototype; document the completed user workflow and backend integration when available.
- Supported modes (Underground, bus, or both) need confirmation.

## Team contributions

Livia Banyai: Back-end development (helper functions, caching), automated test suites (frontend and backend), repository maintenance (updating conftest.py, README, requirements.txt, etc.)
Laura Bonnelame:  Front-end development (html, CSS & JavaScript files), input validation (from the html form), file management and the powerpoint

**To do:** Each team member should review this summary and add any missing contributions.
# TODO: everyone summarise what you've done!
