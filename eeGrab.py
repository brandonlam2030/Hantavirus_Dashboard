import ee
import pandas as pd
import requests
import time

def getCountyFIPS(lat, lon):
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "Counties",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    counties = data["result"]["geographies"].get("Counties", [])
    if counties:
        return counties[0]["GEOID"]  # 5-digit county FIPS
    return None

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
resultDF = pd.DataFrame(columns = ["siteID","decimalLatitude","decimalLongitude","pctDeveloped","pctAgricultural", "pctForest", "pctWetland", "pctWater", "pctBarren", "pctIceSnow"])

developed = {"21", "22", "23", "24"}   
agricultural = {"81", "82"}            
forest = {"41", "42", "43"}   
shrubGrassland = {"52", "71"}         
wetland = {"90", "95"}                 
water = {"11"}                      
barren = {"31"}                      
iceSnow = {"12"}      

for site, coords in neon_sites.items():
    results[site] = get_landcover_composition(coords['decimalLatitude'], coords['decimalLongitude'])
    total = sum(results[site].values())

    pct = dict()
    
    if total > 0:
        for key, value in results[site].items():
            if key in developed:
                pct["developed"] = pct.get("developed", 0) + value
            elif key in agricultural:
                pct["agriculture"] = pct.get("agriculture", 0) + value
            elif key in forest:
                pct["forest"] = pct.get("forest", 0) + value
            elif key in shrubGrassland:
                pct["shrubGrassland"] = pct.get("shrubGrassland", 0) + value
            elif key in wetland:
                pct["wetland"] = pct.get("wetland", 0) + value
            elif key in water:
                pct["water"] = pct.get("water", 0) + value
            elif key in barren:
                pct["barren"] = pct.get("barren", 0) + value
            else:
                pct["iceSnow"] = pct.get("iceSnow", 0) + value
            
        
        newRow = pd.DataFrame([{"siteID": site, "decimalLatitude":coords["decimalLatitude"],"decimalLongitude": coords["decimalLongitude"],"pctDeveloped": pct.get("developed", 0)/total, "pctAgricultural":pct.get("agriculture", 0)/total,"pctForest": pct.get("forest", 0)/total, "pctShrubGrassland": pct.get("shrubGrassland",0)/total,"pctWetland": pct.get("wetland",0)/total, "pctWater": pct.get("water",0)/total, "pctBarren": pct.get("barren", 0)/total,"pctIceSnow": pct.get("iceSnow",0)/total}])
        resultDF = pd.concat([resultDF, newRow], ignore_index = True)    


missingSites = ['BARR', 'BONA', 'DEJU', 'GUAN', 'HEAL', 'LAJA', 'TOOL']
modisSites = {k: v for k, v in neon_sites.items() if k in missingSites}

modisLC = ee.ImageCollection('MODIS/061/MCD12Q1').filter(
    ee.Filter.eq('system:index', '2021_01_01')
).first().select('LC_Type1')

def getModisLandcover(lat, lon, bufferM=1000):
    point = ee.Geometry.Point([lon, lat])
    buffer = point.buffer(bufferM)
    hist = modisLC.reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=buffer,
        scale=500,
        maxPixels=1e9
    ).get('LC_Type1')
    return ee.Dictionary(hist).getInfo()

modisResults = {}
for site, coords in modisSites.items():
    modisResults[site] = getModisLandcover(coords['decimalLatitude'], coords['decimalLongitude'])

developedModis = {13}
agriculturalModis = {12, 14}
forestModis = {1, 2, 3, 4, 5}
shrubGrasslandModis = {6, 7, 8, 9, 10}
wetlandModis = {11}
waterModis = {17}
barrenModis = {16}
iceSnowModis = {15}

for site, coords in modisSites.items():
    total = sum(modisResults[site].values())
    pct = dict()
    if total > 0:
        for key, value in modisResults[site].items():
            key = int(key)
            if key in developedModis:
                pct["developed"] = pct.get("developed", 0) + value
            elif key in agriculturalModis:
                pct["agriculture"] = pct.get("agriculture", 0) + value
            elif key in forestModis:
                pct["forest"] = pct.get("forest", 0) + value
            elif key in shrubGrasslandModis:
                pct["shrubGrassland"] = pct.get("shrubGrassland", 0) + value
            elif key in wetlandModis:
                pct["wetland"] = pct.get("wetland", 0) + value
            elif key in waterModis:
                pct["water"] = pct.get("water", 0) + value
            elif key in barrenModis:
                pct["barren"] = pct.get("barren", 0) + value
            else:
                pct["iceSnow"] = pct.get("iceSnow", 0) + value

        newRow = pd.DataFrame([{
            "siteID": site,
            "decimalLatitude": coords["decimalLatitude"],
            "decimalLongitude": coords["decimalLongitude"],
            "pctDeveloped": pct.get("developed", 0) / total,
            "pctAgricultural": pct.get("agriculture", 0) / total,
            "pctForest": pct.get("forest", 0) / total,
            "pctShrubGrassland": pct.get("shrubGrassland", 0) / total,
            "pctWetland": pct.get("wetland", 0) / total,
            "pctWater": pct.get("water", 0) / total,
            "pctBarren": pct.get("barren", 0) / total,
            "pctIceSnow": pct.get("iceSnow", 0) / total,
            "source": "MODIS"
        }])
        resultDF = pd.concat([resultDF, newRow], ignore_index=True)


crosswalkRows = []
for site, coords in neon_sites.items():
    fips = getCountyFIPS(coords["decimalLatitude"], coords["decimalLongitude"])
    crosswalkRows.append({"siteID": site, "countyFIPS": fips})
    time.sleep(0.2)

crosswalkDF = pd.DataFrame(crosswalkRows)

resultDF = resultDF.merge(crosswalkDF, on="siteID", how="left")
print(resultDF["countyFIPS"].isna().sum())
resultDF.to_csv("data/humanImpact.csv", index=False)

  