import pandas as pd

def getDF():
    return pd.read_csv("aggregatedData.csv")


path = ["data/bloodtest.csv", "data/combined_climate.csv", "data/filtered_precip.csv"]

columns = {path[0]: [["bloodSampleID", "testPathogenName","testResult"], "bloodSampleID"], path[1]: [["date", "lat", "lon", "T2M_MAX", "T2M_MIN"], ["decimalLatitude", "decimalLongitude", "collectDate"], ["lat","lon", "date"]],
           path[2]: [["collectDate", "precipbulk"], "collectDate"]}

parent = pd.read_csv("data/rodent_with_ndvi.csv")
parent = parent[["uid", "nightuid", "namedLocation", "siteID", "decimalLatitude", "decimalLongitude", "coordinateUncertainty", "collectDate", "ndvi", "bloodSampleID"]]
parent['decimalLatitude'] = parent['decimalLatitude'].round(3)
parent['decimalLongitude'] = parent['decimalLongitude'].round(3)


for file in path:
    df = pd.read_csv(file)

    if len(columns[file]) > 2:
        parent = pd.merge(parent,df[columns[file][0]], left_on = columns[file][1], right_on = columns[file][2], how = "left")
    else:
        parent = pd.merge(parent, df[columns[file][0]], on = columns[file][1], how = "left")

parent["testResult"] = parent["testResult"].fillna("Not Tested")
parent["testPathogenName"] = parent["testPathogenName"].fillna("N/A")
parent = parent.drop(columns=['lat', 'lon', 'date'], errors='ignore')
parent["T2M_MAX"] = parent["T2M_MAX"].fillna("N/A")
parent["T2M_MIN"] = parent["T2M_MIN"].fillna("N/A")
parent["precipbulk"] = parent["precipbulk"].fillna("N/A")

parent["ndvi_lag3"] = parent["ndvi"].shift(3)
parent["ndvi_lag5"] = parent["ndvi"].shift(5) 
parent["ndvi_lag6"] = parent["ndvi"].shift(6)  

parent["T2M_MAX_lag1"] = parent["T2M_MAX"].shift(1)
parent["T2M_MAX_lag5"] = parent["T2M_MAX"].shift(5)
parent["T2M_MAX_lag6"] = parent["T2M_MAX"].shift(6)

print(parent["collectDate"].head(5))
print(parent["collectDate"].tail(5))
parent.to_csv("aggregatedData.csv", index = False)


    




    

    