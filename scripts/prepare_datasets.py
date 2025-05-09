# geo_utils.py 를 미리 같은 폴더에 만들어두었다고 가정합니다.
import sys
import os
import numpy as np
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sklearn.neighbors import BallTree

import utils.GEO_UTILS as GU
import utils.CONSTANTS as CONST

def merge_traffic_data(file_map: dict, spot_path: str) -> pd.DataFrame:
    def clean_expressway(filepath):
        df = pd.read_csv(filepath)
        for col in ["2021", "2022", "2023"]:
            df[col] = df[col].astype(str).str.replace(",", "")
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def load_common(filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        df = df.iloc[:, 1:]  # 첫 번째 열 제거 (예: 인덱스나 중복 정보)
        return df

    df_expressway = clean_expressway(file_map["expressway"])
    target_columns = df_expressway.columns.tolist()
    dfs = []

    for key in ["downtown", "boundary", "bridge"]:
        df = load_common(file_map[key])
        df.columns = target_columns
        dfs.append(df)
    
    df_arterial = pd.read_csv(file_map["arterial"])
    df_arterial.columns = target_columns
    dfs.append(df_arterial)
    dfs.append(df_expressway)

    traffic_df = pd.concat(dfs, ignore_index=True)
    spot_df = pd.read_csv(spot_path).drop(columns=["지점명"], errors="ignore")
    traffic_df = pd.concat([traffic_df.reset_index(drop=True), spot_df.reset_index(drop=True)], axis=1)

    return traffic_df

def process_traffic_volume_combined(accident_df: pd.DataFrame, traffic_df: pd.DataFrame, year: int) -> pd.DataFrame:
    print(f"=> {year}년 사고 + 교통량 병합 중...")

    traffic_coords = traffic_df[["lat", "lng", "2021", "2022", "2023"]].copy()
    acc_coords = accident_df[["lat", "lng"]].values
    acc_years = accident_df["acdnt_year"].astype(str).values

    tree = BallTree(np.radians(traffic_coords[["lat", "lng"]].values), metric='haversine')
    distances, indices = tree.query(np.radians(acc_coords), k=1)

    distances_km = distances.flatten() * 6371
    indices = indices.flatten()

    traffic_values = []
    for i, dist in enumerate(distances_km):
        year_str = acc_years[i]
        if dist > 2.0:
            traffic_values.append(np.nan)
            continue

        nearest = traffic_coords.iloc[indices[i]]
        val = nearest[year_str]
        if pd.isna(val):
            fallback = [y for y in ["2021", "2022", "2023"] if y != year_str]
            val = pd.to_numeric(nearest[fallback], errors='coerce').mean()
        traffic_values.append(val)

    accident_df["traffic_volume"] = traffic_values
    return accident_df

def run_all_processing_steps(year, traffic_df):
    print(f"==> {year}년 데이터 통합 처리 시작...\n")

    accident_path = f"./data/raw/all_accident_info_{year}.csv"
    accident_df = pd.read_csv(accident_path)

    # 횡단보도
    crosswalk_df = pd.read_csv("./data/external/crosswalk_data.csv")
    accident_df = GU.mark_zone_proximity_common(
        accident_df, crosswalk_df,
        zone_lat_col="위도", zone_lng_col="경도",
        output_col="near_crosswalk",
        radius_m=10, buffer_m=10
    )

    # 신호등
    light_df = pd.read_csv("./data/external/traffic_light_data.csv")
    accident_df = GU.mark_zone_proximity_common(
        accident_df, light_df,
        zone_lat_col="위도", zone_lng_col="경도",
        output_col="near_traffic_light",
        radius_m=10, buffer_m=10
    )

    # 보호구역
    zone_df = pd.read_csv("./data/external/protection_zone_data.csv")
    for zone_type, col_name in CONST.ZONE_COLUMNS.items():
        sub_df = zone_df[zone_df["구분"] == zone_type]
        accident_df = GU.mark_zone_proximity_common(
            accident_df, sub_df,
            zone_lat_col="위도", zone_lng_col="경도",
            output_col=col_name,
            radius_m=300, buffer_m=100
        )

    # 속도 정보
    def refine(df):
        df = df[df["도로명"].notna() & (df["도로명"].str.strip() != "")]
        df["도로명"] = df["도로명"].str.replace(" ", "").str.strip()
        return df

    def pick_velocity(row):
        code = row["occrrnc_time_code"]
        return (
            row["오전"] if 6 < code < 10 else
            row["낮"] if 11 < code < 14 else
            row["오후"] if 16 < code < 20 else
            row["전일"]
        )

    velocity_df = refine(pd.read_csv(f"./data/raw/{year}velocity.csv"))
    merged_velocity = pd.merge(accident_df, velocity_df, how="inner", left_on="route_nm", right_on="도로명")
    merged_velocity["lanes"] = merged_velocity["차로수"]
    merged_velocity["lengths"] = pd.to_numeric(merged_velocity["연장"].str.replace(",", ""), errors="coerce")
    merged_velocity["velocity"] = merged_velocity.apply(pick_velocity, axis=1)
    accident_df = pd.merge(
        accident_df,
        merged_velocity[["acdnt_no", "lanes", "lengths", "velocity"]],
        how="left",
        on="acdnt_no"
    )
    
    # 교통량
    accident_df = process_traffic_volume_combined(accident_df, traffic_df, year)

    # 저장
    output_path = f"./data/processed/accident_data_{year}.csv"
    accident_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"====> 최종 저장 완료: {output_path}\n")
    
def merge_all_years():
    print("===> 연도별 CSV 전체 병합 중...")
    base_dir = "./data/processed"
    file_names = [f"accident_data_{y}.csv" for y in range(2021, 2024)]
    dfs = [pd.read_csv(os.path.join(base_dir, f)) for f in file_names]
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df.to_csv(os.path.join(base_dir, "accident_data_all.csv"), index=False, encoding="utf-8-sig")
    print("====> 병합 완료: accident_data.csv")    

if __name__ == "__main__":
    
    file_map = {
        "downtown": "./data/raw/traffic_downtown.csv",
        "boundary": "./data/raw/traffic_boundary.csv",
        "bridge": "./data/raw/traffic_bridge.csv",
        "arterial": "./data/raw/traffic_arterial.csv",
        "expressway": "./data/raw/traffic_expressway.csv"
    }
    spot_path = "./data/external/traffic_spot_data.csv"
    traffic_df = merge_traffic_data(file_map, spot_path)
    
    for year in [2021, 2022, 2023]:
        run_all_processing_steps(year, traffic_df)
    
    merge_all_years()

