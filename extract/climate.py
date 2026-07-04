import pandas as pd
import time, os, requests

path = "data/mam_pertrapnight.csv"

rodent = pd.read_csv(path)

# 2. Get unique locations to save time and API bandwidth
unique_locations = rodent[['decimalLatitude', 'decimalLongitude']].drop_duplicates().dropna()

# 3. Create output directory for NASA files
output_dir = "nasa_weather_data"
os.makedirs(output_dir, exist_ok=True)

print(f"Fetching NASA POWER weather data for {len(unique_locations)} unique locations.")

# 4. Loop and request data
for idx, row in unique_locations.iterrows():
    lat = row['decimalLatitude']
    lon = row['decimalLongitude']
    
    filename = f"{output_dir}/nasa_{lat}_{lon}.csv"
    
    # Skip if already downloaded
    if os.path.exists(filename):
        continue
        
    # Construct NASA POWER Daily API URL
    # PRECTOTCORR = Precipitation, T2M_MAX = Max Temp, T2M_MIN = Min Temp
    # community=ag (Agroclimatology community optimized for ecological/soil models)
    start_date = "20160824"
    end_date = "20220909"
    
    nasa_url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=PRECTOTCORR,T2M_MAX,T2M_MIN"
        f"&community=ag&longitude={lon}&latitude={lat}"
        f"&start={start_date}&end={end_date}&format=csv"
    )
    
    try:
        # 1. Fetch the raw text content from NASA
        response = requests.get(nasa_url)
        response.raise_for_status()
        
        # 2. Find exactly how many lines of metadata to skip
        lines = response.text.splitlines()
        header_index = 0
        for i, line in enumerate(lines):
            if "-END HEADER-" in line:
                header_index = i + 1  # The actual data header row is right after this
                break
        
        # 3. Read it into pandas cleanly from that dynamic starting point
        from io import StringIO
        data_string = "\n".join(lines[header_index:])
        location_weather = pd.read_csv(StringIO(data_string))
        
        # 4. Strip any weird whitespace from column names
        location_weather.columns = location_weather.columns.str.strip()
        
        # Save it locally
        location_weather.to_csv(filename, index=False)
        print(f"Successfully downloaded NASA data for: {lat}, {lon}")
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Failed to fetch NASA data for {lat}, {lon}: {e}")