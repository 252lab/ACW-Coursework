# ECM3428 — London Tube Route Planner

The project is focused on developing a route-planning website for journeys in London, using the A* algorithm. It allows the user to plan a journey between two stations using live updates from the tfl API.

## Problem and intended users

Finding the most efficient public-transport route can require comparing multiple possible connections and journey times. This project aims to let a user provide a start stop, end stop, and a start time, and have the program calculate the most efficient route for them.

**Intended users:** People travelling around London who want help planning the most efficient journey along the tube network.

**Current scope:** The project uses London tube stations. The station-coordinate helper filters for Underground NAPTAN IDs.

## Selected algorithm

This project uses A\* algorithm. A\* ranks a candidate station using the journey cost so far, $g(n)$, plus an estimate of the remaining cost to the destination, $h(n)$:

$$f(n) = g(n) + h(n)$$

The A* Algorithm uses a priority queue system to sort through the list of explorable nodes. Each node in the queue has the above f(n) calculated, and the lowest score is added to the explored list, and its neighbours are added to the queue. This is repeated until the end node is added to the explored list.

### Algorithm outline

Inputs: Start_Station, End_Station, Start_Time

The implementation of the algorithm works as thus:
  1) Collect the list of stations that can be reached from the start station in a "route" object, that collects the station, available routes, and times those trains to those other stations leave.
  2) Add the route object that was just collected to a list
  3) For all route objects in the list, get the available stations, and calculate the heuristic + time for each of the available stations.
  4) If there is a shorter path to an explored station in the list, replace the parent node of that station and update the new times.
  5) Select the shortest time from the above calculation, and make a new route object with the parent node pointing to the previous step on the route.
  6) Repeat steps 2-5 until the end station is found.
  7) Reconstruct the shortest route from the chain of nodes and send it to the user. 

### Complexity

A* algorithm base time and space complexities

Time complexity worst-case:

$`O(b^d)`$

Where b is the branching factor – the average number of edges from each node, and d is the number of nodes on the resulting path.
The better the heuristic function the better the complexity is as fewer nodes are visited.
The heuristic function can act as the effective branching factor, the average number of edges chosen to get to the optimal next node. So, the optimal hueristic would be 1, that for every node visited only one edge is taken (so, fewer nodes are visited and the optimal path is immediately taken).

Space complexity:

$`O(b^d)`$

This is the space complexity for the A* algorithm as all nodes must be kep track of in the algorithm (closed list, open list, 

For our algorithm:

$`Nt`$ = Total number of candidate stations

$`K`$ = Total number of nodes expanded in search

$`T`$ = The number of active trains fetched from the api for the given station

$`S`$ = Average number of stops per station

$`(T * S)`$ = The cost of fetching, parsing and saving all valid timetables and stops for each train for a newly expanded station

$`O(K * (Nc * (T * S)))`$

The above is the time complexity for the worste case scenario.

For each route/node (K) which is explored in the A* algorithm it must loop through each of its neighbours (Nt). Then for each of those neighbours it should then loop through every train (T) and fetch each of those trains stops (S). From the list of routes/nodes to be explored the route/node (K) with the shorted heuristic is selected for exploration. When the route/node (K) is selected, a comparison is made to see if the destination station for that route/node matches the desired end station then the algorithm stops, if not the algorithm must continue to loop through all of the available route/nodes in the open list check the neighbours, trains and stops for each until the destination is found.


Link to gemini conversation:

https://share.gemini.google/F0rSXFpPeR3R

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

Our website is not deployed on a server and so will need to be hosted on a local machine. This can be done with the following steps.

- Within your terminal of choice navigate to the app folder within the project repository.
- Run the main.py file.
```sh
python main.py
```
- Click the link produced by this in the terminal and this will open the website within your browser.

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
- **Laura Bonnelame:**  Front-end development (html & CSS files), input validation (for the html form), file management and the powerpoint
- **Rose Burston** Back-end development (hueristic function, fetching train lat and lon information), team coordination (meeting organisation), repository maintenance (README, algorithm complexity)
- **Hannah Wagstaff** Back-end development (getting trains function, a* step function), algorithm design (object definition, algorithm logic), algorithm descriptions (Selected Algorithm, Algorithm Outline in the README)
- **Nur Kinaci** Front-end development (HTML & CSS), reviewing and correcting Flask routing , file management, powerpoint

## AI Statement - TODO

The University of Exeter is committed to the ethical and responsible use of Generative AI (GenAI) tools in teaching and learning, in line with our academic integrity policies where the direct copying of AI-generated content is included under plagiarism, misrepresentation and contract cheating under definitions and offences in TQA Manual Chapter 12.3. To support students in their use of GenAI tools as part of their assessments, we have developed a category tool that enables staff to identify where use of Gen AI is integrated, supported or prohibited in each assessment. This assessment falls under the category of AI Assisted.

AI-supported use is permitted in this assessment. I acknowledge the following uses of GenAI tools in this assessment:
[Yes/No] I have used GenAI tools to assist with research or gathering information.
[Yes] I have used GenAI tools to help me understand key theories and concepts.
[Yes/No] I have used GenAI tools to identify trends and themes as part of my data analysis.
[Yes/No] I have used GenAI tools to suggest a plan or structure for my assessment.
[Yes/No] I have used GenAI tools to give me feedback on a draft.
[Yes/No] I have used GenAI tool to generate image, figures or diagrams.
[Yes/No] I have used GenAI tools to proofread and correct grammar or spelling errors.
[Yes/No] I have used GenAI tools to generate citations or references.
Other: [please specify]
- Proofreading and debugging code and test cases

I declare that I have referenced use of GenAI outputs within my assessment in line with the University referencing guidelines.

