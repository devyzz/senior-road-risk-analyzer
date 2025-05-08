# ──────────────────────────────────────────────────────────────
# 출처 
#
# - 대상: 
# - 방식:  
# - 저장: csv
# -  
# ──────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

def clean_expressway(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    for col in ["2021", "2022", "2023"]:
        df[col] = df[col].astype(str).str.replace(",", "")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def load_common(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df = df.iloc[:, 1:] #### 주석추가!!!!
    return df

def merge_traffic_data(file_map: dict, spot_path: str) -> pd.DataFrame:
    df_expressway = clean_expressway(file_map["expressway"])
    target_columns = df_expressway.columns.tolist()

    dfs = []
    for category in ["downtown", "boundary", "bridge"]:
        df = load_common(file_map[category])
        df.columns = target_columns
        dfs.append(df)

    df_arterial = pd.read_csv(file_map["arterial"])
    df_arterial.columns = target_columns
    dfs.append(df_arterial)
    dfs.append(df_expressway)

    traffic_df = pd.concat(dfs, ignore_index=True)

    spot_df = pd.read_csv(spot_path).drop(columns=["지점명"])
    traffic_df = pd.concat([traffic_df.reset_index(drop=True), spot_df.reset_index(drop=True)], axis=1)

    return traffic_df

def attach_traffic_to_accidents(accident_path: str, traffic_df: pd.DataFrame, output_path: str,
                                 radius_km=2.0, k_neighbors=1):
    accident_df = pd.read_csv(accident_path)
    traffic_coords = traffic_df[['lat', 'lng', '2021', '2022', '2023']].copy()

    accident_coords = accident_df[['lat', 'lng', 'acdnt_year']].copy()
    traffic_radians = np.radians(traffic_coords[['lat', 'lng']].values)
    accident_radians = np.radians(accident_coords[['lat', 'lng']].values)

    knn = NearestNeighbors(n_neighbors=k_neighbors, metric='haversine')
    knn.fit(traffic_radians)
    distances, indices = knn.kneighbors(accident_radians)
    threshold_radians = radius_km / 6371

    traffic_values = []
    for i in range(len(accident_coords)):
        year = str(int(accident_coords.iloc[i]['acdnt_year']))
        dists = distances[i]
        idxs = indices[i]

        vals = []
        for j, dist in enumerate(dists):
            if dist <= threshold_radians:
                try:
                    val = traffic_coords.iloc[idxs[j]][year]
                except KeyError:
                    val = np.nan
                if pd.isna(val) or not isinstance(val, (int, float, np.number)):
                    val = pd.to_numeric(
                        traffic_coords.iloc[idxs[j]][["2021", "2022", "2023"]],
                        errors='coerce'
                    ).mean()
                vals.append(val)

        traffic_values.append(np.mean(vals) if vals else np.nan)

    accident_df['traffic_volume'] = traffic_values
    accident_df.to_csv(output_path, index=False, encoding='utf-8-sig')

def main():
    file_map = {
        "downtown": "./data/raw/traffic_downtown.csv",
        "boundary": "./data/raw/traffic_boundary.csv",
        "bridge": "./data/raw/traffic_bridge.csv",
        "arterial": "./data/raw/traffic_arterial.csv",
        "expressway": "./data/raw/traffic_expressway.csv"
    }
    spot_path = "./data/external/seoul_traffic_spots.csv"

    traffic_df = merge_traffic_data(file_map, spot_path)

    for year in [2021, 2022, 2023]:
        accident_path = f"./data/raw/all_accident_info_{year}.csv"
        output_path = f"./data/processed/accident_data_with_traffic_{year}.csv"
        attach_traffic_to_accidents(accident_path, traffic_df, output_path)

if __name__ == "__main__":
    main()