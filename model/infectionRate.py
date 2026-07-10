import joblib
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

rodentPopBC = joblib.load("model/rodentPopBC.pkl")
og = pd.read_csv("data/aggregatedData.csv")
data = pd.read_csv("model/layerData/layer1.csv")

og = og.merge(data["collect"])

og = og.dropna(subset = ["testPathogenName"]).reset_index()
train = og.groupby(["siteID", "collectDate"])["testResult"].agg(
    totalRecords = "count",
    numPositive = lambda x: (x == "Positive").sum()
)

train["percent"] = train["numPositive"]/train["totalRecords"]

totalPopulation = og.groupby(["siteID","collectDate"]).size().reset_index(name = "population")

bloodSamples = og[og["testResult"] == "Positive"].groupby(["siteID", "collectDate"])["testResult"].count().reset_index()
bloodSamples = bloodSamples.rename(columns = {"testResult":"numPositive"})
totalPopulation = totalPopulation.merge(bloodSamples, how = "left", on = ["siteID","collectDate"])
totalPopulation = totalPopulation.fillna(value = {"numPositive":0})

results = []
def log_curve(t, K, r, t0):
    return K / (1 + np.exp(-r * (t - t0)))

totalPopulation = totalPopulation[["siteID", "collectDate","numPositive", "population"]]

for site, group in totalPopulation.groupby("siteID"):
    if len(group) < 5 or group["numPositive"].sum() == 0: continue

    sitePop = group["population"].cumsum()
    numOfPos = group["numPositive"].cumsum()
    t = (pd.to_datetime(group["collectDate"]) - pd.to_datetime(group["collectDate"].min())).dt.days.values

    try:
        k, _ = curve_fit(log_curve, t, sitePop, p0 = [max(sitePop), .1, np.median(t)], bounds = ([0,0,0],[np.inf, 1.0, max(t)]))
        r,_ = curve_fit(log_curve, t, numOfPos, p0 = [max(numOfPos), .1, np.median(t)], bounds = ([0,0,0],[np.inf, 1.0, max(t)]))

        results.append({"r": r[1], "k": k[0], "siteID": site})

    except RuntimeError:    
        print(f"Site {site} failed to converge.")


risks = pd.DataFrame()
siteFeatures = [col for col in data.columns if col.startswith("siteID_")]

for result in results:
    site = result["siteID"]
    rate = result["r"]
    cap = result["k"]

    
    if f"siteID_{site}" in siteFeatures:
        target = data[data["siteID"] == f"siteID_{site}"]
        expectedRate = rate * (1 + data[""])
    

