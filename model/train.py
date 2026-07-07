from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier as xgb
import pandas as pd

data = pd.read_csv("aggregatedData.csv")

text_columns = data.select_dtypes(include=['object', 'category']).columns

for column in text_columns:
    data[column] = LabelEncoder.fit_transform(data[column])

x_train, x_test, y_train, y_test = train_test_split()