import pandas as pd

path = ["data/bloodtest.csv", "data/combined_climate.csv", "data/precipitation.csv"]

columns = {path[0]: [["bloodSampleID", "testPathogenName","testResult"], "bloodSampleID"], path[1]: [["collectDate", "decimalLongitude", "decimalLatitude", "T2M_MAX", "T2M_MIN"], ["decimalLatitude", "decimalLongitude", "collectDate"]]
           , path[2]: [["siteID","decimalLongitude", "decimalLatitude","collectDate","precipBulk"], ["siteID","collectDate"]]}

parent = pd.read_csv("data/rodent_with_ndvi.csv")
parent = parent[["uid", "nightuid", "namedLocation", "siteID", "decimalLatitude", "decimalLongitude", "coordinateUncertainty", "collectDate", "ndvi", "bloodSampleID"]]
parent['decimalLatitude'] = parent['decimalLatitude'].round(3)
parent['decimalLongitude'] = parent['decimalLongitude'].round(3)



for file in path:
    df = pd.read_csv(file)
    
    if file == path[2] or file == path[1]:
        df["decimalLatitude"] = df["decimalLatitude"].round(3)
        df["decimalLongitude"] = df["decimalLongitude"].round(3)
    parent = pd.merge(parent, df[columns[file][0]], on = columns[file][1], how = "left")


parent = parent.drop(columns=['lat', 'lon', 'date'], errors='ignore')
parent = parent.sort_values(["siteID", "collectDate"])

for col in ["ndvi", "T2M_MAX","T2M_MIN", "precipBulk"]:
    for w in [7,14,30,60]:
        if col == "ndvi":
            parent[f"{col}_lag{w}"] = parent.groupby("siteID")[col].shift(w)
        elif col == "T2M_MAX":
            parent[f"{col}_lag{w}"] = parent.groupby("siteID")[col].transform(lambda x: x.rolling(window = w).mean())
        elif col == "T2M_MIN":
            parent[f"{col}_lag{w}"] = parent.groupby("siteID")[col].transform(lambda x: x.rolling(window = w).mean())
        else:
            parent[f"{col}_lag{w}"] = parent.groupby("siteID")[col].transform(lambda x: x.rolling(window = w).sum())
        

parent = parent.dropna(subset = ["ndvi_lag7","ndvi_lag14","ndvi_lag30","ndvi_lag60","T2M_MAX_lag7","T2M_MAX_lag14","T2M_MAX_lag30","T2M_MAX_lag60","T2M_MIN_lag7","T2M_MIN_lag14","T2M_MIN_lag30","T2M_MIN_lag60","precipBulk_lag7","precipBulk_lag14","precipBulk_lag30","precipBulk_lag60"])
rodentCount = parent.groupby(["siteID", "collectDate"]).size().reset_index(name = "count")
parent = parent.merge(rodentCount, how = "left", on = ["siteID", "collectDate"])
parent["count"] = parent["count"].fillna(0)
parent.to_csv("aggregatedData.csv", index = False)


    




    

    