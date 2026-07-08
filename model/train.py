from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier as xgb
import pandas as pd

data = pd.read_csv("aggregatedData.csv")
data = pd.get_dummies(data, columns=['siteID'])

text_columns = data.select_dtypes(include=['object', 'category']).columns

for column in text_columns:
    data[column] = LabelEncoder.fit_transform(data[column])

data = data.sort_values("collectDate")
split = "2023-01-01"
train = data[data["collectDate"] < split]
test = data[data["collectDate"] >= split]

