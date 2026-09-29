import requests

url = f"https://tfl.gov.uk"

# make the api call
try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses 
    # get the raw JSON response
    data = response.json()
    # print the JSON response
    print(data)
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")