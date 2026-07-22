import pandas as pd

layer1DF = pd.read_csv("model/layerData/layer1.csv")
layer2DF = pd.read_csv("model/layerData/layer2.csv")
humanImpact= pd.read_csv("data/layer3_humanContact.csv")

layer3 = layer2DF.merge(humanImpact, how = "left", on = "siteID")
layer3["RUCC_2023"] = 10 - layer3["RUCC_2023"]

staticCols = ["pctDeveloped", "pctAgricultural", "pctForest", "pctWetland", "pctWater", "pctBarren", "pctIceSnow", "pctShrubGrassland", "RUCC_2023", "Population_2020"]
siteLevel = layer3.drop_duplicates(subset="siteID")[["siteID"] + staticCols].copy()



for column in staticCols:
    mini = siteLevel[column].min()
    maxi = siteLevel[column].max()

    layer3[column] = (layer3[column] - mini) / (maxi - mini) 

dailyCols = ["prevelanceProb", "momentumPred"]
for column in dailyCols:
    mini = layer3[column].min()
    maxi = layer3[column].max()
    layer3[column] = (layer3[column] - mini) / (maxi - mini)

siteLevel = layer3.drop_duplicates(subset="siteID")
correlations = siteLevel[["pctDeveloped", "pctAgricultural", "pctShrubGrassland", 
                            "RUCC_2023", "Population_2020"]].corrwith(siteLevel["prevelanceProb"])
print(correlations)

layer3["contactScore"] = (.2 *  layer3["pctDeveloped"]) + (.2 *  layer3["pctAgricultural"]) + (.2 *  layer3["pctShrubGrassland"]) + (.2 *  layer3["RUCC_2023"]) + (.2 *  layer3["Population_2020"])
layer3["hazardScore"] = (.5 * layer3["prevelanceProb"]) + (.5 * layer3["momentumPred"])
layer3["riskIndex"] = layer3["contactScore"] * layer3["hazardScore"]

print(layer3[["siteID", "riskIndex"]])
layer3.to_csv("final.csv", index = False)
