from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier as xgb
import pandas as pd
import numpy as np
from datetime import date
import joblib

data = pd.read_csv("data/aggregatedData.csv")
data = data.sort_values(by=["siteID", "collectDate"])


data = data.groupby("siteID").apply(lambda x: x.iloc[1:]).reset_index(drop=True)
data["true_percGrowth"] = np.log1p(data["count"]) - np.log1p(data.groupby("siteID")["count"].shift(1).fillna(0))

identifiers = data[["siteID", "collectDate"]].reset_index(drop=True)
data = pd.get_dummies(data, columns=['siteID'])


split = date(2021, 11, 20)

data["collectDate"] = pd.to_datetime(data["collectDate"], format = "%Y-%m-%d", errors = "coerce")
data = data.dropna(subset = ["collectDate"])
data = data.sort_values("collectDate")


train = data[data["collectDate"] < pd.Timestamp(split)]
test = data[data["collectDate"] >= pd.Timestamp(split)]
print(data.columns)

site_features = [col for col in data.columns if col.startswith("siteID_")]

feature_cols = [
    'ndvi_lag7', 'ndvi_lag14', 'ndvi_lag30', 'ndvi_lag60',
    'T2M_MAX_lag7', 'T2M_MAX_lag14', 'T2M_MAX_lag30', 'T2M_MAX_lag60',
    'T2M_MIN_lag7', 'T2M_MIN_lag14', 'T2M_MIN_lag30', 'T2M_MIN_lag60',
    'precipBulk_lag7', 'precipBulk_lag14', 'precipBulk_lag30', 'precipBulk_lag60'
] + site_features

train_x = train[feature_cols]
test_x = test[feature_cols]

train_y = (train["true_percGrowth"] > 0).astype(int)
test_y = (test["true_percGrowth"] > 0).astype(int) # check if your test set column name matches


model = xgb(max_depth=3, learning_rate=0.05, n_estimators=100)
model.fit(train_x, train_y)


prediction_probs = model.predict_proba(test_x)[:, 1]
predictions = model.predict(test_x)

print(f"Model Classification Accuracy: {accuracy_score(test_y, predictions):.4f}")
print(f"AUC-ROC Score (Risk Accuracy): {roc_auc_score(test_y, prediction_probs):.4f}")

data["boomProb"] = model.predict_proba(data[feature_cols])[:, 1]

feature_cols.append("boomProb")
final = pd.concat([identifiers, data], axis=1).reset_index()

final[["siteID", "collectDate", "boomProb"]].to_csv("layer1.csv", index = False)
joblib.dump(model, "model/rodentPopBC.pkl")
