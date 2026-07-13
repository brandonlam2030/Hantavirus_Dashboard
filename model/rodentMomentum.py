import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_absolute_error

data = pd.read_csv("data/aggregatedData.csv")
data["collectDate"] = pd.to_datetime(data["collectDate"])
data = data.sort_values(by=["siteID", "collectDate"])

weather_features = [
    'ndvi_lag120', 'ndvi_lag14', 'ndvi_lag30', 'ndvi_lag60',
    'T2M_MAX_lag120', 'T2M_MAX_lag14', 'T2M_MAX_lag30', 'T2M_MAX_lag60',
    'T2M_MIN_lag120', 'T2M_MIN_lag14', 'T2M_MIN_lag30', 'T2M_MIN_lag60',
    'precipBulk_lag120', 'precipBulk_lag14', 'precipBulk_lag30', 'precipBulk_lag60'
]

data['logCount'] = np.log1p(data['count'])
data['logPrevCount'] = np.log1p(data['prevCount'])


split = pd.Timestamp("2021-11-20")
train = data[data["collectDate"] < split].copy()
test = data[data["collectDate"] >= split].copy()

print(f"Train rows: {len(train)}, Test rows: {len(test)}")


model_momentum = LinearRegression()
X_mom_train = train[['logPrevCount']]
y_mom_train = train['logCount']
model_momentum.fit(X_mom_train, y_mom_train)


train['momentumResiduals'] = y_mom_train - model_momentum.predict(X_mom_train)

X_mom_test = test[['logPrevCount']]
y_mom_test = test['logCount']
test['momentumResiduals'] = y_mom_test - model_momentum.predict(X_mom_test)


model_env = XGBRegressor(
    n_estimators=500,
    learning_rate=0.01,
    max_depth=3,
    subsample=0.8,
    colsample_bytree=0.8
)
model_env.fit(train[weather_features], train['momentumResiduals'])


y_pred_momentum_test = model_momentum.predict(X_mom_test)
mae_momentum_test = mean_absolute_error(y_mom_test, y_pred_momentum_test)
r2_momentum_test = r2_score(y_mom_test, y_pred_momentum_test)

predicted_residuals_test = model_env.predict(test[weather_features])
mae_env_test = mean_absolute_error(test['momentumResiduals'], predicted_residuals_test)

improvement = ((mae_momentum_test - mae_env_test) / mae_momentum_test) * 100

print("\n--- HELD-OUT TEST SET RESULTS ---")
print(f"Momentum Baseline R-squared (test): {r2_momentum_test:.4f}")
print(f"Momentum Baseline MAE (test): {mae_momentum_test:.4f}")
print(f"Residual Model (XGBoost) MAE (test): {mae_env_test:.4f}")
print(f"Model Improvement by adding weather (test, out-of-sample): {improvement:.2f}%")

print("\nFeature Importance of Weather Modulators (fit on train only):")
importance = pd.Series(model_env.feature_importances_, index=weather_features)
print(importance.sort_values(ascending=False))


data['log_prevCount_pred_input'] = data['logPrevCount']
data['momentumPred'] = model_momentum.predict(data[['logPrevCount']])
data['momentumResidualsFull'] = data['logCount'] - data['momentumPred']
data['env_residual_pred'] = model_env.predict(data[weather_features])

data['relative_anomaly'] = data.groupby('siteID')['count'].transform(lambda x: (x - x.mean()) / x.std())
data['relative_anomaly'] = data['relative_anomaly'].fillna(0)

final_export = data[['siteID', 'collectDate', 'count', 'relative_anomaly', 'momentumResidualsFull', 'env_residual_pred']]
final_export = final_export.rename(columns={'momentumResidualsFull': 'momentumResiduals'})
final_export.to_csv("model/layerData/layer1.csv", index=False)

joblib.dump(model_momentum, "model/rodentMomentum.pkl")
print("\n'layer1.csv' has been generated for Layer 2 consumption.")
print("NOTE: reported metrics above are from the held-out test set only — this is the honest, generalizable performance estimate.")