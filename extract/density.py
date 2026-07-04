import pandas as pd

dfs = [pd.read_csv(f) for f in ["data/populationData/density.csv","data/populationData/urban.csv","data/populationData/agriculture.csv","data/populationData/forest.csv"]]
dfs = [df.melt(id_vars=["Country Name","Country Code"], var_name="year", value_name=name)
       for df, name in zip(dfs, ["density","urban","agri","forest"])]
df = dfs[0].merge(dfs[1], on=["Country Name","Country Code","year"]) \
           .merge(dfs[2], on=["Country Name","Country Code","year"]) \
           .merge(dfs[3], on=["Country Name","Country Code","year"])
df = df.dropna()