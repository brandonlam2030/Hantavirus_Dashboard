import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score,GroupKFold
from sklearn.metrics import roc_auc_score


data = pd.read_csv("model/layerData/layer1.csv")
agg = pd.read_csv("data/aggregatedData.csv")
blood = pd.read_csv("data/bloodtest.csv")

blood["isPositive"] = (blood["testResult"] == "Positive").astype(int)

blood["isPositive"] = (blood["testResult"] == "Positive").astype(int)

blood_daily = blood.groupby(["siteID", "collectDate"], as_index=False).agg(
    n_tested=("isPositive", "count"),
    n_positive=("isPositive", "sum")
)
blood_daily["prevalance"] = (blood_daily["n_positive"] > 0).astype(int)

data = data.merge(blood_daily[["collectDate", "siteID", "prevalance"]], how = "left", on = ["collectDate", "siteID"])
features = [
    'ndvi_lag120', 'ndvi_lag14', 'ndvi_lag30', 'ndvi_lag60',
    'T2M_MAX_lag120', 'T2M_MAX_lag14', 'T2M_MAX_lag30', 'T2M_MAX_lag60',
    'T2M_MIN_lag120', 'T2M_MIN_lag14', 'T2M_MIN_lag30', 'T2M_MIN_lag60',
    'precipBulk_lag120', 'precipBulk_lag14', 'precipBulk_lag30', 'precipBulk_lag60', "siteID", "collectDate"
]
data = data.merge(agg[features], how = "left", on = ["siteID", "collectDate"])

features.pop()
features.pop()
features.append("momentumPred")
data["collectDate"] = pd.to_datetime(data["collectDate"])
data = data.sort_values(by = ["siteID", "collectDate"])


modelData = data.copy().dropna(subset = ["prevalance"])

for col in features:
    modelData[col + "_siteAnom"] = modelData.groupby("siteID")[col].transform(lambda x: x - x.mean())
    data[col + "_siteAnom"] = data.groupby("siteID")[col].transform(lambda x: x - x.mean())

for idx in range(len(features)):
    features[idx] = features[idx] + "_siteAnom"

gkf = GroupKFold(n_splits=5)
groups = modelData["siteID"]
y = modelData["prevalance"]

groupScores = []
for train_idx, test_idx in gkf.split(modelData[features], y, groups=groups):
    foldModel = XGBClassifier(max_depth=3, learning_rate=.05, n_estimators=100)
    foldModel.fit(modelData[features].iloc[train_idx], y.iloc[train_idx])
    foldProba = foldModel.predict_proba(modelData[features].iloc[test_idx])[:, 1]
    groupScores.append(roc_auc_score(y.iloc[test_idx], foldProba))

print(f"GroupKFold AUC by fold: {groupScores}")
print(f"GroupKFold mean AUC: {np.mean(groupScores):.4f} (this is the honest, reportable performance number)")


model = XGBClassifier(max_depth=3, learning_rate=.05, n_estimators=100)
model.fit(modelData[features], y)

data["prevelanceProb"] = model.predict_proba(data[features])[:,1]
finalExport = data[["siteID", "collectDate", "count", "prevelanceProb", "momentumPred"]]
finalExport.to_csv("model/layerData/layer2.csv", index = False)
