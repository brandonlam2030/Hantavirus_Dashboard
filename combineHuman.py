import pandas as pd
pd.set_option('display.max_columns', None)
df = pd.read_csv('final.csv')

# Mississippi River is roughly at -90 longitude
df['region'] = df['decimalLongitude'].apply(lambda lon: 'West' if lon < -90 else 'East')

regionSummary = df.groupby(['siteID','region'])['riskIndex'].mean().reset_index()
print(regionSummary.groupby('region')['riskIndex'].describe())
print()
print(regionSummary.sort_values('riskIndex', ascending=False).to_string())