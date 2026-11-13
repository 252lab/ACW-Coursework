# ACW Coursework

A pathfind algorithm implementation.

Website used to plan a bus journey in london.

## Virtual Environment Setup

### Linux / macOS (bash, zsh)

```
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows (cmd)

```
python -m venv .venv
.venv\Scripts\activate.bat
```

### Installing required packages

```
pip install -r requirements.txt
```

## Linting

Run the project lint checks from the activated virtual environment.

Example usage for black, flake8, and isort:
```
black .
```

Example usage for ruff:
```
ruff check .
```

## Running the program

Currently, the backend can be run using `python3 python/main.py`.
As the project progresses, this will form part of the overall web app.

Website link: https://252lab.github.io/ACW-Coursework

## Data sources

TfL API: https://api.tfl.gov.uk

## Team members and responsibilities:

Livia Banyai: Back-end development (helper functions, caching), automated test suites (frontend and backend), repository maintenance (updating conftest.py, README, requirements.txt, etc.)

# TODO: everyone summarise what you've done!
