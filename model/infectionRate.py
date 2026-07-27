import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
import joblib
import plotly.graph_objects as go

def getTopFactorsChart(top = 6):

    model = joblib.load("model/layerData/layer2_model.joblib")
    features = joblib.load("model/layerData/layer2_features.joblib")
    importance_dict = model.get_booster().get_score(importance_type='gain')
    imp_series = pd.Series(importance_dict)


    imp_series = imp_series.reindex(features, fill_value=0)
    imp_series = imp_series.sort_values(ascending=False)


    imp_series = imp_series / imp_series.sum()


    def prettify(name):
        name = name.replace("_siteAnom", "")
        replacements = {
            "ndvi": "NDVI",
            "T2M_MAX": "Max Temp",
            "T2M_MIN": "Min Temp",
            "precipBulk": "Precipitation",
            "momentumPred": "Rodent Momentum",
        }
        for key, label in replacements.items():
            if name.startswith(key):
                lag = name.split("lag")[-1] if "lag" in name else None
                base = label
                return f"{base} ({lag}d)" if lag else base
        return name

    labels = [prettify(f) for f in imp_series.index]


    top_labels = labels[:top][::-1]
    top_values = imp_series.values[:top][::-1]


    fig = go.Figure(go.Bar(
        x=top_values,
        y=top_labels,
        orientation='h',
        marker=dict(color='#3fae6a', cornerradius=8),
        text=[f"{v:.2f}" for v in top_values],
        textposition='outside',
        textfont=dict(color='white', size=13),
    ))

    fig.update_layout(
        title=dict(text="Top Contributing Factors (Global)", font=dict(color='white', size=16)),
        plot_bgcolor='#2D5133',
        paper_bgcolor='#2D5133',
        xaxis=dict(visible=False, range=[0, max(top_values)*1.2]),
        yaxis=dict(tickfont=dict(color='white', size=12), showgrid=False),
        margin=dict(l=10, r=30, t=50, b=10),
        height=450,
    )

    return fig

def getInfectionScore():
    layer2 = pd.read_csv("model/layerData/layer2.csv")

    return layer2["score"].mean()


if __name__ == "__main__":

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
    data["predictions"] = model.predict(data[features])
    finalExport = data[["siteID", "collectDate", "count", "prevelanceProb", "momentumPred", "predictions"]]
    finalExport["score"] = np.mean(groupScores)
    finalExport.to_csv("model/layerData/layer2.csv", index = False)

    joblib.dump(model, "model/layerData/layer2_model.joblib")
    joblib.dump(features, "model/layerData/layer2_features.joblib")
