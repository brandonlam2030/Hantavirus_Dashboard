import os
import time
import pandas as pd
import ee
 
# ---------------------------------------------------------------------------
# 0. CONFIG — edit these
# ---------------------------------------------------------------------------
RODENT_CSV_PATH = "data/mam_pertrapnight.csv"   # must have columns: decimalLongitude, decimalLatitude, collectDate
GEE_PROJECT_ID = "hantavirus-data"     # required by Earth Engine now, even free tier
 
# Absolute path avoids the "ran successfully but I can't find the file" problem —
# this always writes to the same folder as this script, regardless of your working directory.
OUTPUT_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rodent_with_ndvi.csv")
 
COORD_ROUND = 3   # ~111m precision, roughly matches MODIS 250m pixel — coarsen if your sites are denser than this is meaningful for
 
print(f"Script running from: {os.path.dirname(os.path.abspath(__file__))}")
print(f"Output will be written to: {OUTPUT_CSV_PATH}")
 
# ---------------------------------------------------------------------------
# 1. LOAD + DEDUP
# ---------------------------------------------------------------------------
rodent_df = pd.read_csv(RODENT_CSV_PATH)
 
# Strip whitespace from column names -- a common silent cause of "column not found"
# errors when a CSV has a stray leading/trailing space in its header row.
rodent_df.columns = rodent_df.columns.str.strip()
 
required_cols = ['decimalLongitude', 'decimalLatitude', 'collectDate']
missing_cols = [c for c in required_cols if c not in rodent_df.columns]
if missing_cols:
    raise KeyError(
        f"Expected columns {missing_cols} not found in your CSV.\n"
        f"Actual columns in your file: {rodent_df.columns.tolist()}\n"
        f"Fix the column names above (or edit required_cols) to match your real data."
    )
 
rodent_df['collectDate'] = pd.to_datetime(rodent_df['collectDate'])
 
rodent_df['lat_r'] = rodent_df['decimalLatitude'].round(COORD_ROUND)
rodent_df['lon_r'] = rodent_df['decimalLongitude'].round(COORD_ROUND)
rodent_df['year_month'] = rodent_df['collectDate'].dt.to_period('M').astype(str)
 
unique_points = (
    rodent_df[['lat_r', 'lon_r', 'year_month']]
    .drop_duplicates()
    .reset_index(drop=True)
)
 
print(f"\nRodent rows: {len(rodent_df):,}")
print(f"Unique (location, month) pairs: {len(unique_points):,}")
 
if len(unique_points) > 200_000:
    print("WARNING: still very dense after rounding. Consider coarsening COORD_ROUND "
          "further, or snapping to a fixed grid, before running this against Earth Engine.")
 
# ---------------------------------------------------------------------------
# 2. NDVI VIA GOOGLE EARTH ENGINE (MODIS MOD13Q1, 250m, 16-day composites)
# ---------------------------------------------------------------------------
ee.Authenticate()  # opens a browser prompt the first run, cached after that
ee.Initialize(project=GEE_PROJECT_ID)
 
 
def get_ndvi_for_month(points_df: pd.DataFrame, year_month: str, batch_size: int = 500) -> pd.DataFrame:
    """Batch-extract NDVI for all unique points in a given month."""
    year, month = year_month.split('-')
    start = f"{year}-{month}-01"
    end = (pd.Period(year_month) + 1).start_time.strftime("%Y-%m-%d")
 
    collection = (
        ee.ImageCollection("MODIS/061/MOD13Q1")
        .filterDate(start, end)
        .select(["NDVI", "SummaryQA"])
    )
 
    if collection.size().getInfo() == 0:
        return pd.DataFrame(columns=['row_id', 'ndvi_raw', 'qa'])
 
    image = collection.mean()
 
    records = []
    # Chunk within the month too — reduceRegions can choke or throttle on very large FeatureCollections
    for start_idx in range(0, len(points_df), batch_size):
        chunk = points_df.iloc[start_idx:start_idx + batch_size]
        features = [
            ee.Feature(ee.Geometry.Point([row.lon_r, row.lat_r]), {'row_id': int(i)})
            for i, row in chunk.iterrows()
        ]
        fc = ee.FeatureCollection(features)
 
        sampled = image.reduceRegions(collection=fc, reducer=ee.Reducer.first(), scale=250)
 
        try:
            result = sampled.getInfo()
        except Exception as e:
            print(f"  GEE batch failed for {year_month} rows {start_idx}-{start_idx+batch_size}: {e}")
            time.sleep(5)
            continue
 
        for feat in result['features']:
            props = feat['properties']
            records.append({
                'row_id': props.get('row_id'),
                'ndvi_raw': props.get('NDVI'),
                'qa': props.get('SummaryQA'),
            })
 
    return pd.DataFrame(records)
 
 
ndvi_frames = []
months = unique_points['year_month'].unique()
print(f"\nExtracting NDVI for {len(months)} unique months...")
 
for i, ym in enumerate(months):
    month_points = unique_points[unique_points['year_month'] == ym].reset_index(drop=True)
    result = get_ndvi_for_month(month_points, ym)
    if result.empty:
        print(f"  [{i+1}/{len(months)}] {ym}: no MODIS coverage, skipping")
        continue
    # NOTE: do not set result['year_month'] here -- month_points already carries
    # a year_month column, and merging two frames that both have a same-named
    # non-key column silently renames both to year_month_x/year_month_y instead
    # of erroring, which quietly drops the plain 'year_month' column downstream.
    result = result.merge(
        month_points.reset_index().rename(columns={'index': 'row_id'}),
        on='row_id'
    )
    ndvi_frames.append(result)
    print(f"  [{i+1}/{len(months)}] {ym}: {len(result)} points extracted")
 
ndvi_df = pd.concat(ndvi_frames, ignore_index=True) if ndvi_frames else pd.DataFrame()
 
if not ndvi_df.empty:
    # Raw NDVI is scaled by 10000 in MOD13Q1 -- convert to standard -1..1 range
    ndvi_df['ndvi'] = ndvi_df['ndvi_raw'] / 10000.0
    # SummaryQA: 0 = good data, 1 = marginal, 2 = snow/ice, 3 = cloudy. Drop anything worse than "marginal".
    bad_qa = ndvi_df['qa'] > 1
    print(f"\nDropping {bad_qa.sum()} of {len(ndvi_df)} NDVI values flagged low-quality (cloud/snow) by SummaryQA")
    ndvi_df.loc[bad_qa, 'ndvi'] = None
 
# ---------------------------------------------------------------------------
# 3. JOIN BACK TO THE FULL RODENT TABLE
# ---------------------------------------------------------------------------
merged = rodent_df.copy()
 
if not ndvi_df.empty:
    merged = merged.merge(
        ndvi_df[['lat_r', 'lon_r', 'year_month', 'ndvi']],
        on=['lat_r', 'lon_r', 'year_month'],
        how='left'
    )
else:
    merged['ndvi'] = None
    print("\nWARNING: no NDVI data was extracted at all -- check GEE auth/project setup.")
 
# ---------------------------------------------------------------------------
# 4. REPORT MISSINGNESS -- DO NOT SKIP THIS, CHECK IT BEFORE MODELING
# ---------------------------------------------------------------------------
print("\n--- Missingness report ---")
print(f"NDVI missing: {merged['ndvi'].isna().mean() * 100:.1f}%")
print("If this is high (>15-20%), check: MODIS coverage only starts in Feb 2000, "
      "and confirm decimalLatitude/decimalLongitude are WGS84, not a projected CRS.")
 
merged.to_csv(OUTPUT_CSV_PATH, index=False)
print(f"\nSaved merged panel to: {OUTPUT_CSV_PATH}")
print(f"Rows: {len(merged):,}")