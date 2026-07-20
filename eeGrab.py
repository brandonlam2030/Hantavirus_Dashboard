import ee
import pandas as pd

ee.Authenticate()
ee.Initialize(project="hantavirus-data")

df = pd.read_csv("data/rodent_with_ndvi.csv")
df = df.drop_duplicates(subset = ["siteID"])

neon_sites = df.set_index("siteID")[["decimalLongitude","decimalLatitude"]].to_dict(orient = "index")

nlcd_collection = ee.ImageCollection('USGS/NLCD_RELEASES/2021_REL/NLCD')
nlcd = nlcd_collection.filter(ee.Filter.eq('system:index', '2021')).first().select('landcover')

def get_landcover_composition(lat, lon, buffer_m=1000):
    point = ee.Geometry.Point([lon, lat])
    buffer = point.buffer(buffer_m)
    
    hist = nlcd.reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=buffer,
        scale=30,
        maxPixels=1e9
    ).get('landcover')
    
    return ee.Dictionary(hist).getInfo()  # {class_code: pixel_count, ...}

# run for each site, convert pixel counts to % of buffer area
results = {}
for site, coords in neon_sites.items():
    results[site] = get_landcover_composition(coords['decimalLatitude'], coords['decimalLongitude'])

humanPresence = {"21", "22", "23", "24"}
agriculture = {"81","82"}
natural = {"42", "42", "43", "52", "71"}