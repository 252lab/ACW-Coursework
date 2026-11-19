# ECM3428 — London Tube Route Planner

The project is focused on developing a route-planning website for journeys in London, using the A* algorithm.

(NOTE: add more details once the project is finished)

## Problem and intended users

Finding the most efficient public-transport route can require comparing multiple possible connections and journey times. This project aims to let a user provide a start stop, end stop, and a start or end time, and have the program calculate the most efficient route for them.

**Intended users:** People travelling around London who want help planning the most efficient journey along the tube network.

**Current scope:** The project uses London tube stations. The station-coordinate helper filters for Underground NAPTAN IDs.

## Selected algorithm

This project uses A\* algorithm. A\* ranks a candidate station using the journey cost so far, $g(n)$, plus an estimate of the remaining cost to the destination, $h(n)$:

$$f(n) = g(n) + h(n)$$

### Algorithm outline

(NOTE: fill this in once the project has been finished.)

### Complexity

*A* algorithm base time and space complexities*

Time complexity worst-case:

O(b^d)

Where b is the branching factor – the average number of edges from each node, and d is the number of nodes on the resulting path.
The better the heuristic function the better the complexity is as fewer nodes are visited.
The heuristic function can act as the effective branching factor, the average number of edges chosen to get to the optimal next node. So, the optimal hueristic would be 1, that for every node visited only one edge is taken (so, fewer nodes are visited and the optimal path is immediately taken).

Space complexity:

O(b^d)

This is the space complexity for the A* algorithm as all nodes must be kep track of in the algorithm (closed list, open list, 

For our algorithm:

Nt = Total number of candidate stations

K = Total number of nodes expanded in search

T = The number of active trains fetched from the api for the given station

S = Average number of stops per station

(T * S) = The cost of fetching, parsing and saving all valid timetables and stops for each train for a newly expanded station

O(K * (Nc * (T * S)))

This is for the worst case scenario. As for each node which is explored in the A* algorithm (K) you must for each of it's neighbours (Nc) fetch all of it's trains (T) and then fetch each of those trains stops (S). Then comparisons are made to see which routes have the smallest heuristic, and once a rout/Node (K) is finally found for which it's destination station matches the desired end station then the algorithm stops.

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

- Route-search behaviour and the A\* heuristic have not yet been fully validated; confirm heuristic units match the journey-time units.
- Transfer/waiting-time calculation and use of live arrival predictions need verification.
- The station-coordinate CSV path is currently relative to the process working directory and can fail when launched from the repository root.
- Route-journey tests currently fail because of that CSV path; the two faster-route test functions are placeholders.
- The current website is a prototype; document the completed user workflow and backend integration when available.
- Supported modes (Underground, bus, or both) need confirmation.
- The program currently only works for one repetitions.
- The program cannot stop finding route halfway through safely.

## Team contributions

- **Livia Banyai:** Back-end development (helper functions, caching), automated test suites (frontend and backend), repository maintenance (updating conftest.py, README, requirements.txt, etc.)
- **Laura Bonnelame:**  Front-end development (html, CSS & JavaScript files), input validation (from the html form), file management and the powerpoint

**To do:** Each team member should review this summary and add any missing contributions.
