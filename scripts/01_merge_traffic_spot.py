# ──────────────────────────────────────────────────────────────
# traffic 데이터 전처리 + 사고 데이터와 병합
# - 대상: 서울시 교통량 정보 + 공공데이터포털 지점별 교통량 통계 데이터
# - 작업: 
#   • 연도별 교통량 데이터를 통합 후 위치정보(위도/경도)와 병합
#   • 사고지점과 가장 가까운 교통량 측정지점을 찾아 해당 연도의 교통량 매핑
#   • 교통량 값이 없을 경우 해당 지점의 다른 연도 평균값으로 보완
# ──────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree


def clean_expressway(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    for col in ["2021", "2022", "2023"]:
        df[col] = df[col].astype(str).str.replace(",", "")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_common(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df = df.iloc[:, 1:]  # 첫 번째 열 제거 (예: 인덱스나 중복 정보)
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

    spot_df = pd.read_csv(spot_path).drop(columns=["지점명"])  # 지점명 제거
    traffic_df = pd.concat([traffic_df.reset_index(drop=True), spot_df.reset_index(drop=True)], axis=1)

    return traffic_df


def attach_traffic_to_accidents(accident_path: str, traffic_df: pd.DataFrame, output_path: str, radius_km=2.0):
    accident_df = pd.read_csv(accident_path)
    traffic_coords = traffic_df[["lat", "lng", "2021", "2022", "2023"]].copy()

    accident_coords = accident_df[["lat", "lng", "acdnt_year"]].copy()
    traffic_radians = np.radians(traffic_coords[['lat', 'lng']].values)
    accident_radians = np.radians(accident_coords[['lat', 'lng']].values)

    tree = BallTree(traffic_radians, metric='haversine')
    distances, indices = tree.query(accident_radians, k=1)

    distances_km = distances.flatten() * 6371
    indices = indices.flatten()

    traffic_values = []
    for i in range(len(accident_coords)):
        year = str(int(accident_coords.iloc[i]['acdnt_year']))

        if distances_km[i] > radius_km:
            traffic_values.append(np.nan)
            continue

        nearest_idx = indices[i]
        nearest_row = traffic_coords.iloc[nearest_idx]

        val = nearest_row[year]
        if pd.isna(val) or not isinstance(val, (int, float, np.number)):
            all_years = ["2021", "2022", "2023"]
            fallback_years = [y for y in all_years if y != year]
            val = pd.to_numeric(nearest_row[fallback_years], errors='coerce').mean()

        traffic_values.append(val)

    accident_df["traffic_volume"] = traffic_values
    accident_df.to_csv(output_path, index=False, encoding="utf-8-sig")


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