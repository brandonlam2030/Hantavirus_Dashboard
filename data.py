import pandas as pd
from sheets import worksheet, coords

def load_cases():
    values = worksheet.get_all_values()
    return pd.DataFrame(values[1:], columns=values[0])

def load_coordinates():
    coordinates = pd.DataFrame(coords.get_all_values(), columns=["country", "lat", "lon", "count", "population"])
    coordinates = coordinates[1:].reset_index(drop=True)
    coordinates["count"] = coordinates["count"].astype("float32")
    coordinates["population"] = coordinates["population"].astype(int)
    coordinates["lat"] = coordinates["lat"].astype("float32")
    coordinates["lon"] = coordinates["lon"].astype("float32")
    coordinates = coordinates[coordinates["count"] > 0]
    
    return coordinates


