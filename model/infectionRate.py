import joblib
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

momentum = joblib.load("model/rodentMomentum.pkl")
data = pd.read_csv("model/layerData/layer1.csv")
bloodtest = pd.read_csv("data/bloodtest.csv")
aggregated = pd.read_csv("data/aggregatedData.csv")

data["collectDate"] = pd.to_datetime(data["collectDate"])
aggregated["collectDate"] = pd.to_datetime(aggregated["collectDate"])
bloodtest["collectDate"] = pd.to_datetime(bloodtest["collectDate"])

raw_counts = aggregated[["siteID", "collectDate", "count", "prevCount"]].copy()
raw_counts["collectDate"] = pd.to_datetime(raw_counts["collectDate"])

data = data.drop(columns=["count"], errors="ignore")
data = data.merge(raw_counts, on=["siteID", "collectDate"], how="left")

data = data.merge(bloodtest[["collectDate", "siteID", "testPathogenName", "testResult"]], how = "left", on = ["collectDate","siteID"])
data = data.fillna(value = {"numPositive": 0})


data = data.dropna(subset = ["testPathogenName"]).reset_index()
train = data.groupby(["siteID", "collectDate"])["testResult"].agg(
    totalRecords = "count",
    numPositive = lambda x: (x == "Positive").sum()
)

train["percent"] = train["numPositive"]/train["totalRecords"]

totalPopulation = data[["siteID","collectDate", "count"]].drop_duplicates()
train = train.merge(totalPopulation, on = ["siteID","collectDate"], how = "left")

print(totalPopulation)
results = []
def log_curve(t, K, r, t0):
    return K / (1 + np.exp(-r * (t - t0)))


for site, group in train.groupby("siteID"):
    if len(group) < 5 or group["numPositive"].sum() == 0: continue

    sitePop = group["count"]
    numOfPos = group["numPositive"].cumsum()
    t = (pd.to_datetime(group["collectDate"]) - (group["collectDate"].min())).dt.days.values
    t = t / 30

    try:
        k, _ = curve_fit(log_curve, t, sitePop, p0 = [max(sitePop), .1, np.median(t)], bounds = ([0,0,0],[np.inf, .3, max(t)]))
        r,_ = curve_fit(log_curve, t, numOfPos, p0 = [max(numOfPos), .1, np.median(t)], bounds = ([0,0,0],[np.inf, .3, max(t)]))

        results.append({"r": r[1], "k": k[0], "siteID": site})

    except RuntimeError:    
        print(f"Site {site} failed to converge.")

print(results)

risks = pd.DataFrame()
data["predictedPopulation"] = np.nan

data['logPrevCount'] = np.log1p(data['prevCount'])
data["predictedPopulation"] = np.expm1(momentum.predict(data[["logPrevCount"]]))

for result in results:
    site = result["siteID"]
    rate = result["r"]
    cap = result["k"]

    mask = data["siteID"] == site
    data.loc[mask, "expectedRate"] = rate * (1 + data.loc[mask, "predictedPopulation"] / cap)

final = data[["siteID", "collectDate", "count", "prevCount", "predictedPopulation", "expectedRate"]]
final = final.drop_duplicates()

print(data["expectedRate"])
final.to_csv("model/layerData/layer2.csv", index = False)
print("Layer 2 data successfully exported!")


