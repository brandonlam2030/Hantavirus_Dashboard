import pandas as pd
import numpy as np


path = ["data/bloodtest.csv"]

columns = {path[0]: [["bloodSampleID", "testPathogenName","testResult"], "bloodSampleID"]}

parent = pd.read_csv("data/rodent_with_ndvi.csv")
parent = parent[["uid", "nightuid", "namedLocation", "siteID", "decimalLatitude", "decimalLongitude", "coordinateUncertainty", "collectDate", "ndvi", "bloodSampleID"]]
parent['decimalLatitude'] = parent['decimalLatitude'].round(3)
parent['decimalLongitude'] = parent['decimalLongitude'].round(3)

climate = pd.read_csv("data/combined_climate.csv")
climate["decimalLatitude"] = climate["decimalLatitude"].round(3)
climate["decimalLongitude"] = climate["decimalLongitude"].round(3)
climate["collectDate"] = pd.to_datetime(climate["collectDate"], format="%Y-%m-%d")


site_coords = parent[["siteID", "decimalLatitude", "decimalLongitude"]].drop_duplicates()
climate = climate.merge(site_coords, on=["decimalLatitude", "decimalLongitude"], how="left")

climate = climate.sort_values(["siteID", "collectDate"]).set_index("collectDate")

for w in [14, 30, 60, 120]:
    climate[f"T2M_MAX_lag{w}"] = climate.groupby("siteID")["T2M_MAX"].transform(lambda x: x.rolling(f"{w}D").mean())
    climate[f"T2M_MIN_lag{w}"] = climate.groupby("siteID")["T2M_MIN"].transform(lambda x: x.rolling(f"{w}D").mean())
    climate[f"precipBulk_lag{w}"] = climate.groupby("siteID")["PRECTOTCORR"].transform(lambda x: x.rolling(f"{w}D").sum())

climate = climate.reset_index()

for file in path:
    df = pd.read_csv(file)
    print(file)
    df = df.sort_values(["bloodSampleID","testedDate"])
    
    df["hasResult"] = df["testResult"].notna()
    df = df.sort_values(["bloodSampleID", "testedDate", "hasResult"])
    before = len(df)
    df = df.drop_duplicates(subset = "bloodSampleID", keep = "last").drop(columns = "hasResult")

    parent = pd.merge(parent, df[columns[file][0]], on = columns[file][1], how = "left")


parent = parent.drop(columns=['lat', 'lon', 'date'], errors='ignore')
parent = parent.sort_values(["siteID", "collectDate"])

parent["isTested"] = parent["testResult"].notna()
parent["isPositive"] = (parent["testResult"] == "Positive").astype(int)

daily = parent.groupby(["siteID", "collectDate"], as_index=False).agg(
    ndvi = ("ndvi", "mean"),
    nTested = ("isTested", "sum"),
    nPositive = ("isPositive", "sum"),
)

daily["count"] = parent.groupby(["siteID","collectDate"]).size().values
daily["prevalence"] = daily["nPositive"]/daily["nTested"].where(daily["nTested"] > 0)
daily = daily.sort_values(["siteID", "collectDate"])

visits_per_site = daily.groupby("siteID").size()

daily["collectDate"] = pd.to_datetime(daily["collectDate"], format = "%Y-%m-%d")
daily = daily.set_index("collectDate")


for w in [14, 30, 60, 120]:
        daily[f"ndvi_lag{w}"] = daily.groupby("siteID")["ndvi"].transform(
            lambda x: x.rolling(f"{w}D").mean()
        )
        
daily = daily.reset_index()
daily = daily.dropna(subset=[c for c in daily.columns if "_lag" in c])
daily["prevCount"] = daily.groupby("siteID")["count"].shift(1)
daily = daily[daily["prevCount"].notna()]
daily["true_percGrowth"] = np.log1p(daily["count"]) - np.log1p(daily["prevCount"])

daily = daily.sort_values("collectDate")
climate = climate.sort_values("collectDate")

lag_cols = [c for c in climate.columns if "_lag" in c]

daily = pd.merge_asof(
    daily,
    climate[["siteID", "collectDate"] + lag_cols],
    on="collectDate",
    by="siteID",
    direction="backward"
)

print()
print("Final aggregatedData.csv shape:", daily.shape)
print("Site-days with n_tested > 0 in final output:", (daily["nTested"] > 0).sum())
print("Site-days with n_positive > 0 in final output:", (daily["nPositive"] > 0).sum())

daily.to_csv("data/aggregatedData.csv", index = False)



    




    

    