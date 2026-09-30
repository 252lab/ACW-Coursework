import requests
import pandas as pd

# filters to only bus routes, doesn't include other modes of transport
url = "https://api.tfl.gov.uk/Line/Mode/bus" 

# make the api call
try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses 
    # get the raw JSON response
    data = response.json()
    # print the JSON response as a table
    df = pd.DataFrame(data)
    # print(df)
    # inspect columns
    print(df.columns)
    # inspect id and name columns
    print(df[['id', 'name']])
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")